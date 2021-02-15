import tornado.ioloop
import tornado.web


class Register(tornado.web.RequestHandler):

    def get(self):
        self.render("./templates/register.html", title="Register")

    def post(self):
        self.write("You wrote " + self.get_body_argument("username"))
        print(self.get_body_argument("username"))
        # register user logic here
        self.redirect(r"/home")


class Login(tornado.web.RequestHandler):

    def get(self):
        self.render("./templates/login.html", title="Login")

    def post(self):
        self.write("You wrote " + self.get_body_argument("username"))
        print(self.get_body_argument("username"))
        # register user logic here
        self.redirect(r"/home")
