# Minimal example

# Where is this hosted?
top_url = "https://www.ty-penguin.org.uk/spigot-example"

# N.B. This example code includes a check for the existence of a 
# rule in robots.txt, denying access to this application. This is
# a safety check to ensure you don't just roll this out and leave 
# it open to "legitimate" crawlers.
#
# You need something like the following in your site's robots.txt
# file:
#
# User-agent: *
# Disallow: /spigot-example

import sys, os, re
from datetime import datetime
from urllib.robotparser import RobotFileParser

# Make sure the install directory is in the Python path.
home = os.path.dirname(os.path.realpath(__file__))
if home not in sys.path:
    sys.path.append(home)

# Bring in the Spigot class.
from spigot import Spigot

# Safety check: If a robots.txt file doesn't exist or doesn't disallow
# access to this application, refuse to start. Obviously, if you remove
# this check, you're opening yourself up to all sorts of "fun".

# Parse out the root of the hosting site.
site_top = re.match("^(https?://[^/]*).*?$", top_url)
if not site_top:
    print(f"Failed to match site part out of top URL {top_url}")
    exit(1)

# Construct the URL to its robots.txt file.
robots_txt = site_top.group(1) + "/robots.txt"

# Python handily supplies a class for checking robots.txt behaviour.
rp = RobotFileParser()
rp.set_url(robots_txt)
rp.read()

# Does robots.txt deny access to the application's top URL? If not,
# refuse to start
if rp.can_fetch("*", top_url):
    print(f"Refusing to start since {robots_txt} doesn't block {top_url}")
    exit(1)

# Create the application object that mod_wsgi uses.
application = Spigot(
    # Pass the "home" directory. If this isn't specified,
    # the Spigot class will assume it can find other Python
    # modules and the templates in  the same directory as 
    # the class.
    home_dir = home,

    # The top URL of the site. This is passed into templates so they can
    # generate links to other pages in the hierarchy.
    top_url = top_url,

    # The earliest "date" in the blog. Page links will be generated
    # with dates between this date and the current date.
    blog_start_date = datetime(2012, 8, 14, 12, 0, 0).timestamp(),

    # Spigot seeds the random number generator with a value derived
    # from the page URL. This means that URLs are "static" - revisiting
    # the same URL will generally give you the same page content.
    #
    # For the top level "index", I thought it would be nice if you could
    # specify the random seed - it allows you to try a few values and see
    # which gives the most pleasing gibberish.
    top_page_seed = 42,

    # Load management: How many outstanding requests are allowed before
    # Spigot will give a HTTP 503 error, and what percentage of (one) CPU
    # should we limit it to.
    #
    # If you're using mod_wsgi, I'd suggest putting spigot into its own
    # process group and setting max_thread_queue_len to one less than the
    # number of threads in the group. This means that there should always be
    # enough spare resources to display the top level page.
    max_thread_queue_len = 9,
    max_cpu_percent = 20,
)
