from .site_route import site_route
from .pipe_route import pipe_route
from .login_route import login_route
from .loginck_route import loginck_route
from .images_route import images_route
from .kafka_route import kafka_route
from .chart_route import chart_route
from .news_route import news_route

blueprints = [
   (site_route,"/"),
   (pipe_route,"/api/pipe"),
   (login_route,"/api/login"),
   (loginck_route,"/api/loginck"),
   (images_route,"/api/images"),
   (kafka_route,"/api/logs"),
   (chart_route,"/api/chart"),
   (news_route,"/api/news"),
]



def register_blueprints(app):
    app.secret_key = 'your-secret-key-here'
    for blueprint,prefix in blueprints:
        app.register_blueprint(blueprint,url_prefix=prefix)