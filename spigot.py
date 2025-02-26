import os, random, re, time, hashlib, struct
import queue
from datetime import datetime
from urllib.parse import quote
from flask import Flask, request, render_template, abort

from markovchain import MarkovChain
from loadmanager import LoadManager

class Spigot(Flask):
    # This class doesn't define the following methods. If you
    # define them in a derived class, they will be called:

    # The abort hook is called whenever a connection is aborted.
    # It should return the 503 error message. You might use this,
    # for example, to flag that an abort has happened.
    #
    # Update: if you return a tuple (http_code, content) then,
    # if the code is 200, a normal page will be returned, otherwise
    # the abort will be called with the code and content. This allows
    # you to replace an abort with a real page. Beware, though, that
    # the abort functionality is triggered when the spigot has exceeded
    # the thread queue length, so whatever you do to generate content
    # needs to be very light on CPU.
    #
    # I've made this change because I've got an idea for caching a few
    # thousand recently generated pages and, when we're out of resources,
    # just returning one of those randomly. Should be very quick and should
    # continue to generate garbage even under high request rates.
    #
    # def abort_hook(self):
    #     return "Please try again later"

    # The page pre-hook is called before page content has been created. This
    # function is passed a dict containing the tags that Jinja2 will be
    # passed, and the random.Random() instance that was used to create
    # the page. Your hook can modify this dict.
    #
    # def page_pre_hook(self, jinja_tags, rng):
    #     jinja_tags["extra_stuff"] = 42
  
    # The page post-hook is called after page content has been created. This
    # function is passed the generated content. You might use this hook to
    # maintain access stats.
    #
    # def page_post_hook(self, content):
    #     self.total_size += len(content)
  
    # The top hook is called after top "index" page content 
    # has been created, in a similar manner to the page hook.
    #
    # def top_pre_hook(self, jinja_tags, rng):
    #     jinja_tags["extra_stuff"] = 42

    def __init__(self,
                top_url,
                blog_start_date=None,
                min_page_len=2000,
                max_page_len=20000,
                top_page_len=2500,
                top_page_seed=42,
                top_page_link_list_target_len=30,
                home_dir=None,
                markov_input="markov_input.txt",
                markov_memory_length=8,
                max_thread_queue_len=0,
                max_cpu_percent=50
            ):

        # Home dir not specified: use directory of current file.
        if home_dir is None:
            home_dir = os.path.dirname(os.path.realpath(__file__))

        # Start date not specified - use 10 years ago.
        if blog_start_date is None:
            blog_start_date = int(time.time() - 10*365*24*60*60)

        # Save the bits we need elsewhere.
        self.top_url = top_url
        self.home_dir = home_dir
        self.blog_start_date = blog_start_date
        self.min_page_len = min_page_len
        self.max_page_len = max_page_len
        self.top_page_len = top_page_len
        self.top_page_seed = top_page_seed
        self.top_page_link_list_target_len = top_page_link_list_target_len

        # Create the Markov Chain using the specified input
        # file.
        self.markov = MarkovChain(
            f"{home_dir}/{markov_input}", 
            markov_memory_length
        )

        # Create the load manager.
        self.loadmanager = LoadManager(
            max_queue_len = max_thread_queue_len,
            target_pcpu = max_cpu_percent
        )

        # Start the Flask application.
        super().__init__("server",
            template_folder=f"{home_dir}/templates",
            static_folder=f"{home_dir}/static"
        )
        self.config["TEMPLATES_AUTO_RELOAD"] = True

        # Register URL paths.
        self.add_url_rule("/", view_func=self.top_router, methods=["GET"])
        self.add_url_rule("/<path:location>", view_func=self.page_router, methods=["GET"])

    # Top level page has a predefined title and gets a short
    # article and a long list of links.
    def top_router(self):
        # Fixed seed so the content and list of links on the 
        # page is fixed (more or less).
        rng = random.Random(self.top_page_seed)

        # Make a list of dated links. We step through the date range of the
        # "blog", aiming for approximately the number of links requested.
        #
        # roundedtime is used to choose the target interval so that the
        # list of links doesn't change constantly. It'll change roughly
        # every 3 months, and will have additions (recent posts) during
        # the 3 month period.
        link_list = []
        now = time.time()
        interval = (self.roundedtime(90) - self.blog_start_date) // self.top_page_link_list_target_len

        stamp = self.blog_start_date
        while stamp < now:
            title, date, url = self.datedlink(stamp, rng=rng)

            # Add to the list, most recent first.
            link_list.insert(0, [ url, date + ": " + title ])

            # Step forward by amount randomly centred on the interval needed
            # to make the list length close to that requested.
            stamp += rng.randint(interval//2, interval*3//2)

        # Put in default jinja tags and call the top hook for
        # extra stuff to be put in, if needed.
        tags = {
            "top_url":     self.top_url,
            "markov_text": self.pagetext(rng),
            "link_list":   link_list,
        }
        if hasattr(self, "top_pre_hook"):
            self.top_pre_hook(tags, rng)

        # Finally render the template with the collected info.
        return render_template("index.tpl", **tags)

    # All other pages get much longer content and next/previous
    # links.
    def page_router(self, location):
        # Serialise page generation using LoadManager.
        try:
            with self.loadmanager:
                content = self.page(location)
                if hasattr(self, "page_post_hook"):
                    self.page_post_hook(content)
            return content
        except queue.Full:
            if hasattr(self, "abort_hook"):
                # abort_hook can now return either a string or 
                # a http code and a string. In the latter case,
                # if the code is 200 then a normal return is
                # done with the content, else the code is passed
                # to abort along with the content.
                hook_output = self.abort_hook()
                if isinstance(hook_output, str):
                    abort(503, hook_output)
                elif isinstance(hook_output, tuple) or isinstance(hook_output, list):
                    code, content = hook_output
                    if code != 200:
                        abort(code, content)
                    else:
                        return content
                else:
                    abort(503, "Try again later")
            else:
                abort(503, "Try again later")

    def page(self, location):
        # Seed the random number generator based on the
        # location string. That means each "url" will have
        # the same Markov output.
        #
        # The line below is fairly horrible, but ensures that all
        # parts of the location contribute to seeding the random number
        # generator.
        rng = random.Random(struct.unpack("L", hashlib.md5(location.encode("utf-8")).digest()[:8])[0])
        current_url = location

        # If the location looks like a dated article of the form  
        # 2025/01/03/title/, make a date for the page and strip it
        # off the URL path.
        m = re.match(r"^(\d{4})/(\d{2})/(\d{2})/(.+)/$", location)
        if m:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 12, 0, 0)
            stamp = dt.timestamp()
            ordinal = (["th", "st", "nd", "rd"] + ["th"] * 6)[dt.day % 10]
            if dt.day > 9 and dt.day < 20:
                ordinal = "th"
            page_date = dt.strftime(f"%e{ordinal} %B %Y")
            location = m.group(4)
        else:
            stamp = rng.randint(self.blog_start_date, int(time.time()))
            page_date = ""

        # Make a page title. The following line uses self.markov to 
        # generate a short sentence, seeding it with the incoming URL.
        # This means the page title will bear some relation to the 
        # page URL. The re.split tries to ensure that the title is 
        # just a single sentence.
        seedtitle = location.replace("_", " "). \
                capitalize(). \
                replace(" i ", " I "). \
                replace(" i'", "I'")
        page_title, _, _ = self.datedlink(time.time(), seedtitle, target_len=60, rng=rng)

        # Generate short Markov output to make "earlier" and "later" links.
        earlier, date, earlier_url = self.datedlink(stamp - rng.randint(86400*2, 86400*30), rng=rng)
        later, date, later_url =  self.datedlink(stamp + rng.randint(86400*2, 86400*30), rng=rng)

        # Create an initial list of tags for jinja.
        tags = {
            "top_url":     self.top_url,
            "markov_text": self.pagetext(rng),
            "title":       page_title,
            "pagedate":    page_date,
            "current":     page_title,
            "current_url": current_url,
            "earlier":     earlier,
            "later":       later,
            "earlier_url": earlier_url, 
            "later_url":   later_url,
        }

        # Call page_pre_hook, which might change or augment tags.
        if hasattr(self, "page_pre_hook"):
            self.page_pre_hook(tags, rng)
                
        # Finally, render the "page" template, using what we've gathered.
        return render_template("page.tpl", **tags)

    # This generates a page title, a formatted date and
    # a link of the form 2025/01/02/title/.
    def datedlink(self, stamp, seed_text=None, rng=random, target_len=30):
        if stamp < self.blog_start_date or stamp > time.time():
            return None, None, None

        dt = datetime.fromtimestamp(stamp)

        # We expect the link title to be truncated for display, so just
        # collect a few words.
        words = self.markov.generate(0, seed_text, rng=rng)[:-1].replace("/", " ").split()
        title = []
        title_len = 0
        while len(words) > 0 and title_len < target_len:
            title_len += len(words[0])+1
            title.append(words[0])
            words = words[1:]
        title = " ".join(title)

        date = dt.strftime("%Y-%m-%d")
        url = dt.strftime("%Y/%m/%d/") + quote(re.sub(r"[ %]", "_", title.lower()))+"/"
        return title, date, url

    # Return a target length for a page.
    # I've separated this function out so that it can
    # be overridden by a derived class. For my own version
    # of spigot, I'm using a power law to generate a distribution
    # of page sizes that more closely matches other pages on my site.
    def targetlength(self, rng):
        return rng.randint(self.min_page_len, self.max_page_len)

    # Create the "markov" tag - a number of paragraphs.
    def pagetext(self, rng=random):
        text = ""
        paragraphs = self.markov.generate(self.targetlength(rng), rng=rng)
        for para in paragraphs:
            # Add a realistic link to each paragraph.
            pos = rng.randint(0, len(para))

            # Match into:
            #     (1) the first {pos} characters,
            #     (2) any non-whitespace characters,
            #     (3) any whitespace characters,
            #     (4) two wordlike things
            #     (5) the rest of the string.
            # We'll glue the first three together, stick an "a href" around
            # the fourth, glue the fifth back on and skip pos to just after
            # where we modified.
            m = re.match(r"^(.{"+str(pos)+"}\S*\s+)([A-Za-z']+\s+[a-z']+)(\s+.*)$", para, re.S)
            if m:
                # Don't make links on short text.
                if len(m.group(2)) > 3:
                    _, _, url = self.datedlink(rng.randint(self.blog_start_date, self.roundedtime(90)), rng=rng)
                    para = m.group(1) + f"""<a href="{self.top_url}/{url}/">{m.group(2)}</a>""" + m.group(3)
            text += "<p>\n" + para + "\n"
        return text

    # Generate a timestamp value, rounded to a specified
    # number of days. e.g. roundedtime(31) would return 
    # 1st January for the whole of January.
    def roundedtime(self, days):
        return int(time.time()/86400/days)*86400*days

