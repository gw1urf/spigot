# What is it?

This is a simple proof of concept of using a Markov Chain to 
generate an infinitely large website.

spigot.py contains a class, Spigot, which you can subclass to provide
extra functionality if you want. It implements a simple Flask application
which you could serve from Apache's mod_wsgi, for example.

The hierarchy that's generated is intended to look like a blog, with a 
top level "index" page and individual dated "posts" hosted at URLs below
the top level..

The code is very much designed around speed, since my own install is seeing
upwards of 40,000 hits per hour and has seen extended periods ove over
80,000 hits/hour. I hope it's still reasonably readable, though - I've tried
not to make its workings too obscure in the seach for optimisation.

I'm not going to give too much detail in how to use this code, at this
point. If you're not fairly familiar with deploying web applications and
managing web server load, you probably don't want to be playing with this!

# What do I need?

* Python and Flask. On Debian, ```apt-get install python3-flask``` should
  get you all you need.
* A working web server with the ability to run Python WSGI applications.
  For example, Apache with mod_wsgi.

# How is it structured

The "templates" directory contains Jinja2 templates for the top level page
and "posts".

The Markov chain expects to find a file named "markov_input.txt" containing
some plain ascii text. This is read and its content is then used to generate
the gibberish within the pages. I've supplied an example containing some
Sherlock Holmes stories, since they're in the public domain. For my own
installation, I've used the entire text of my own blog. It does a reasonable
job of parroting my writing style.

index.py file contains an example of using Spigot under Apache's mod_wsgi.
For this, you'd want something like the following in your Apache config.

    WSGIDaemonProcess spigot threads=10 maximum-requests=10000 user=spigot-user group=spigot-group
    WSGIScriptAlias /spigot-example /path/to/spigot/base/index.py process-group=spigot application-group=%{GLOBAL}

In the above, ```spigot-user``` and ```spigot-group``` are the username and 
groupname of a user that the application should run as.

# Safety

Web crawlers can be quite aggressive and, if they are poorly written and
happen to hit an install of Spigot, they could easily cause high hit rates
on your server. The application attempts to limit the impact of aggressive
crawlers by limiting CPU and thread usage, but you can still run into 
problems - e.g. apache logs filling your disk.

To an extent, this is a global problem, since aggressive crawlers are likely
already hitting your web server. But by providing an infinitely large
tree of pages, you're just asking for lots of hits.

As a slight protection, the example index.py includes a check to prevent
it running unless under a URL that's blocked in your site's robots.txt
file. You could, of course, remove this check if you wished.
