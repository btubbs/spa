import spa
from spa.static import StaticHandler

routes = (
    ('/', '', StaticHandler, {'directory': '.'}),
)
app = spa.App(routes)

spa.run(app)

# Now navigate to localhost:8000/simple_static.py and you should see this file
# served out to you.
