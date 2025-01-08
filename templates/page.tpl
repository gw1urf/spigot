<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{title}}</title>
</head>
<body>
{% if pagedate == "" %}
<h1>{{title}}</h1>
{% else %}
<h1>{{pagedate}}: {{title}}</h1>
{% endif %}

<p>
<a href="{{top_url}}">Top</a><br>
{% if earlier_url %}
Previous post: <a href="{{top_url}}/{{earlier_url}}">{{earlier | truncate(40, false) }}</a><br>
{% endif %}
Current post: <a href="./" style="width: 33%;">{{current | truncate(40, false) }}</a><br>
{% if later_url %}
Next post: <a href="{{top_url}}/{{later_url}}" style="width: 33%;">{{later | truncate(40, false) }}</a><br>
{% endif %}

<p>
{{markov}}

</body>
</html>

