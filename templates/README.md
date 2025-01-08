Jinja templates go here. The application uses index.tpl for the top
level page of the infinite tree and page.tpl for pages below the top.

The top level page gets handed a small amount of Markov text and a 
collection of link details to fake pages below the top.

A "page" gets handed a (possibly longer) set of Markov text and
link details for an "earlier" and "later" page.

With a bit of formatting, this structure can be made to look like 
a blog.
