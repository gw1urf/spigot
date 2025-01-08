<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>An infinite maze of twisty little pages</title>
  </head>
<body>
<h1>An infinite maze of twisty little pages</h1>

<p>
Everything is imaginary. Nothing is real. 

<p>
{{markov_text}}

<ul>
{% for link in link_list %}
<li> <a href="{{top_url}}/{{link[0]}}">{{ link[1] | truncate(30, false) }}</a>
{% endfor %}
</ul>

</body>
</html>
