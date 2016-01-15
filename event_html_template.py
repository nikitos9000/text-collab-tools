content_template = """<html>
	<head>
		<style>
			.diff-html-added {
				background-color: #99FF99;
			}

			.diff-html-removed {
				background-color: #FF9999;
			}
		</style>
	</head>
	<body>
		%s
	</body>
</html>"""

positive_changes_template = """<span class="diff-html-added">%s</span>"""
negative_changes_template = """<span class="diff-html-removed">%s</span>"""
section_template = """<strong>%s</strong>"""

text_templates = [ ("\n", "<br/>") ]
