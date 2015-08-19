"""
This script shows how to use Spa's smart static files view, which automatically
serves static files with md5 hash segments in their paths for cache busting
purposes.
"""
import os

import spa
from spa.static.smart import SmartStatic, get_hash, add_hash_to_filepath
from werkzeug.wrappers import Response


# Build up some HTML for the homepage with some MD5ed links.

def get_link(filepath):
    with open(filepath) as f:
        file_hash = get_hash(f)

    url = add_hash_to_filepath('/files/' + os.path.basename(filepath), file_hash)
    return '<li><a href="{url}">{url}</a></li>'.format(url=url)

here = os.getcwd()
links = [get_link(p) for p in os.listdir(here) if os.path.isfile(p)]
homepage = """
This page demonstrates how Spa can serve static files that have content-based
hashes in their filenames, and how you can use those as links in your own
homepage.  Under normal use cases you'd use these URLs in &lt;link> and
&lt;script> tags.
<ul>
{links}
</ul>
""".format(links='\n'.join(links))


def home(*args, **kwargs):
    return Response(homepage, content_type='text/html')

routes = (
    ('/', 'home', home),
    ('/files/<path:filepath>', 'static', SmartStatic(directory='.')),
)
app = spa.App(routes)

spa.run(app)

# Now navigate to localhost:8000/simple_static.py and you should see this file
# served out to you.
