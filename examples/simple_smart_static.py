from spa.static.smart import SmartStatic
import spa

routes = (
    ('/<path:filepath>', '', SmartStatic(directory='.')),
)

app = spa.App(routes)

spa.run(app)
