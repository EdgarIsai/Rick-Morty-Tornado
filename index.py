import tornado.ioloop
import tornado.web
from tornado.httpclient import AsyncHTTPClient
import motor.motor_tornado


class Register(tornado.web.RequestHandler):
    """
    Register an user, it'll only allow one unique username,
    Same user cannod be registered twice
    """

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def get(self):
        if self.current_user:
            self.redirect("/login")
            return  # return is necessary, if not specified it'll try to self.render after finish
        self.render("./templates/register.html", title="Register")

    async def post(self):
        db = self.settings['db']
        # Search if the user already exists
        user = db.users.find(
            {'username': self.get_body_argument("username")}
        )
        user = await user.to_list(length=100)
        count = 0

        for doc in user:
            count += 1
        # If it exists, it can't be registered again
        if count >= 1:
            self.write("That user already exists")
        else:
            document = {
                'username': self.get_body_argument("username"),
                'password': self.get_body_argument("password")
            }

            result = await db.users.insert_one(document)

            self.set_secure_cookie("user", self.get_body_argument("username"))
            self.redirect("/home")


class Login(tornado.web.RequestHandler):
    """
    If you are already logged in, you'll get redirected to /home
    if not you can log in using proper credentials
    """

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def get(self):
        if self.current_user:
            self.redirect("/home")
            return  # return is necessary, if not specified it'll try to self.render after finish
        self.render("./templates/login.html", title="Login")

    async def post(self):
        # register user logic here
        db = self.settings['db']
        user = db.users.find(
            {'username': self.get_body_argument("username")})
        user = await user.to_list(length=100)
        if user:
            if user[0]["password"] == self.get_body_argument("password"):
                # The cookie is needed to identify if the user is already logged in
                self.set_secure_cookie(
                    "user", self.get_body_argument("username")
                )
                self.redirect("/home")
            else:
                self.redirect("/login")  # if incorrect credentials
        else:
            self.redirect("/login")  # if the user does not exist


class Home(tornado.web.RequestHandler):
    """
    Display the characters and let you choose one so you can comment on it
    """

    def get_current_user(self):
        return self.get_secure_cookie("user")

    async def get(self):
        if not self.current_user:
            self.redirect("/login")
            return  # return is necessary, if not specified it'll try to self.render after finish
        # Fetch asynchronously the characters and set the data as json
        http = tornado.httpclient.AsyncHTTPClient()
        response = await http.fetch(
            "https://rickandmortyapi.com/api/character"
        )
        json = tornado.escape.json_decode(response.body)
        json = json["results"]
        self.render("./templates/home.html", characters=json)


class Character(tornado.web.RequestHandler):
    """
    Display a specific character and let you write a comment, which will be stored
    in a mongodb db
    """

    def get_current_user(self):
        return self.get_secure_cookie("user")

    async def get(self, id):
        if not self.current_user:
            self.redirect("/login")
            return  # return is necessary, if not specified it'll try to self.render after finish
        # Fetch for the specific character you choose based on the character id
        http = tornado.httpclient.AsyncHTTPClient()
        response = await http.fetch(
            "https://rickandmortyapi.com/api/character/"+str(id)
        )
        json = tornado.escape.json_decode(response.body)
        db = self.settings['db']
        subcollection = 'character' + str(id)
        # Search through the db to see if there are any comments for the character
        comments = db.comments[subcollection].find(
            {})
        comments = await comments.to_list(length=100)
        self.render("./templates/character.html",
                    character=json, comments=comments)

    async def post(self, id):
        """ Let you add a comment to the character """
        document = {"comment": self.get_body_argument(
            "comment"), "author": self.current_user}
        db = self.settings['db']
        subcollection = 'character' + str(id)
        result = await db.comments[subcollection].insert_one(document)
        print('result %s' % repr(result))
        self.redirect(r"/character/"+str(id))


def make_app():
    db = motor.motor_tornado.MotorClient().tornado_app

    return tornado.web.Application([
        (r"/", Register),
        (r"/login", Login),
        (r"/home", Home),
        (r"/character/([0-9]+)", Character)
    ], db=db, cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__")


if __name__ == "__main__":
    app = make_app()
    app.listen(3000)
    tornado.ioloop.IOLoop.current().start()
