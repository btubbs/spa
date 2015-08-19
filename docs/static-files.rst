Static Files
============

StaticHandler
-------------

Spa includes helpers for making it easy to serve static files from your Python
application.  The first of those is a StaticHandler class that is just
configured as a regular route when setting up your application.  For an app that
did nothing but serve static files, your entire app could be as simple as this::

    import spa
    from spa.static import StaticHandler

    routes = (
        ('/<path:filepath>', '', StaticHandler, {'directory': '.'}),
    )
    app = spa.App(routes)

    spa.run(app)

When setting up your route for StaticHandler, you must have a 'filepath'
parameter in the URL, as in the example above.

The StaticHandler class is useful for serving JS and CSS files in development.

SmartStatic
-----------

In production you have to worry about performance and scalability.  For static
files, that means using caching.  Caching means you have to worry about cache
invalidation.  And the gold standard for doing cache invalidation with static
files is for the file URL to include a hash of the file's actual contents.  That
way it becomes impossible for your app's HTML to include a link to a stale file.
So instead of having something like this in your homepage::

    <script src="/js/app.js"></script>

You'd have something like this::

    <script src="/js/app.de12adbe34ef.js"></script>

The "de12adbe34ef" part is 12 characters of an MD5 hash of the actual contents
of app.js.  That way if you ever change app.js and re-deploy your app, the URL
to app.js will change to point to the new version, and you don't have to worry
about users getting a stale, cached copy of app.js.

Spa implements a 'SmartStatic' class that handles all of this for you.  Here's a
simple example of using it::

    from spa.static.smart import SmartStatic
    import spa

    routes = (
        ('/<path:filepath>', '', SmartStatic(directory='.')),
    )

    app = spa.App(routes)

    spa.run(app)

In that example, all the files in the current working directory will be served
at the root path, but will *only* be accessible if the requested path contains
the first 12 character's of the file's MD5 sum, just before the file extension.

The above example is available in examples/simple_smart_static.py in the Spa
repository.  Try running this command from the root of the repository::

    python examples/simple_smart_static.py

You should see a server start up.  Then try navigating to
http://localhost:8000/LICENSE.2c73ef712574.txt.  You should see the contents of
Spa's LICENSE.txt file. (Note, if we ever update LICENSE.txt, like to change the
effective copyright date, this link will break.)

In addition to serving files with hashes in their names, Spa will also *modify
the contents* of any `@import` or `url()` directives in your CSS files (if they
refer to other URLs in your app), so that their URLs will have hashes in them.

NOTE: All of the file renaming is done in memory, the first time a file is
requested from the application.  There is no need to run an extra step at build
time to rename files, update CSS contents, and persist them all to disk, as you
may be familiar with from Django's "collectstatic" command.

With this cache busting mechanism in place, your static files can be served from
behind a content distribution network (CDN) with extremely long expiration times
set in its HTTP headers.  This is the recommended method for serving static
files with Spa.
