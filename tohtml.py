import sys
import os
from shutil import copytree
import string

def error(msg):
	print("Error: "+msg)

def warn(msg):
	print("Warning: "+msg)

begin_character = "\\"
end_character = ">"
table_cell_separator_character = "|"

html_escaped_characters = {
	"<": "&lt;",
	">": "&gt;",
	"&": "&amp;"
}

code_highlighting_needed = False

style_string = ""

def escape(text, replacements):
    return ''.join(replacements.get(c, c) for c in text)

def escape_html(text):
	return escape(text, html_escaped_characters)

type_0_set = {
	begin_character: escape_html(begin_character),
	end_character: escape_html(end_character),
	table_cell_separator_character: escape_html(table_cell_separator_character),
	" ": " ",
	"x": "<input type=\"checkbox\" checked>",
	"o": "<input type=\"checkbox\">",
	"r": "<hr>"
}

type_1_set = {
	"b": "b",
	"i": "i",
	"u": "u",
	"h": "mark",
	"s": "del",
	"v": "sub",
	"^": "sup",
	"q": "blockquote"
}

def parse_link(text):
    url, *text_parts = text.strip().split(" ", 1)
    return f"<a href=\"{url}\">{' '.join(text_parts)}</a>" if text_parts else f"<a href=\"{url}\">{url}</a>"

def parse_format(text):
	global code_highlighting_needed
	code_highlighting_needed = True
	new_text = ""
	auto_format = True
	if text[0] in string.whitespace:
		new_text = text[1:]
	else:
		i = 0
		while text[i] not in string.whitespace:
			i += 1
		text_format = text[:i]
		new_text = text[i+1:]
		auto_format = False
	text_format_html_string = "" if auto_format else f" class=\"{text_format}\""
	return f"<pre><code{text_format_html_string}>{new_text}</code></pre>"

def parse_embeded(text):
	return f"<embed src=\"{text}\">"

def parse_table(text):
	output_text = ""
	rows = [line.split("|") for line in text.split("\n")]
	max_cols = max(len(row) for row in rows)
	for row in rows:
		output_text += "<tr>"
		for i, cell_text in enumerate(row):
			if i == len(row)-1:
				colspan = max_cols-i
			else:
				colspan = 1
			output_text += f"<td colspan=\"{colspan}\">{cell_text.strip()}</td>"
		output_text += "</tr>"

	return f"<table><tbody>{output_text}</tbody></table>"

type_2_set = {
	"l": parse_link,
	"e": parse_embeded,
	"f": parse_format,
	"t": parse_table
}

def parse(text):
	output_text = ""
	tag_stack = []
	i = 0
	def c():
		return text[i]
	while i < len(text):
		if c() == begin_character:
			i += 1
			if c() in [str(i) for i in range(1, 7)]:
				h_number = c()
				text_block = ""
				i += 1
				while i<len(text) and c() != "\n":
					text_block += text[i]
					i += 1
				output_text += f"<h{h_number}>{text_block}</h{h_number}>"
			elif c() in type_0_set.keys():
				output_text += type_0_set[c()]
			elif c() in type_1_set.keys():
				tag_name = type_1_set[c()]
				output_text += f"<{tag_name}>"
				tag_stack.append(tag_name)
			elif c() in type_2_set.keys():
				sub_parse = type_2_set[c()]
				text_block = ""
				i += 1
				while i < len(text) and c() != end_character:
					text_block += escape_html(c())
					i += 1
				output_text += sub_parse(text_block)
			else:
				warn("unknown special character \""+c()+"\" at character "+str(i))
				output_text += type_0_set[begin_character]+c()
		elif c() == end_character:
			if len(tag_stack)>0:
				output_text += f"</{tag_stack.pop()}>"
			else:
				warn("end character with no matching begin character at character "+str(i))
				output_text += type_0_set[end_character]
		else:
			output_text += c()
		i += 1
	for tag in tag_stack:
		warn("unmatch opened tag " + tag)
	return f"<!DOCTYPE html><html><head><title>note</title><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><style>{style_string}</style><link rel=\"stylesheet\" href=\"./highlight/styles/base16/isotope.min.css\"><script src=\"./highlight/highlight.min.js\"></script><script>hljs.highlightAll();</script></head><body>{output_text}</body></html>"

def main():
	if len(sys.argv) == 1 or len(sys.argv)>3:
		error("wrong number of arguments")
		sys.exit(1)
	inFile = sys.argv[1]
	outFile = os.path.splitext(sys.argv[2] if len(sys.argv)==3 else inFile)[0]+".html"

	try:
		with open(inFile, "r") as f:
			text = f.read()
	except:
		error("error reading the note file")
		sys.exit(1)

	replacements = {}
	for c in list(set(html_escaped_characters.keys()).difference(set([begin_character, end_character, table_cell_separator_character]))):
		replacements[c] = html_escaped_characters[c]
	escaped_text = escape(text, replacements)

	warn("the character positions in warnings and errors might be offset because of html escaping \"<\", \">\" and \"&\"")

	main_directory = os.path.dirname(sys.argv[0])

	try:
		with open(os.path.join(main_directory, "style.css"), "r") as f:
			global style_string
			style_string = f.read()
	except:
		error("error reading the style file")

	html = parse(escaped_text)

	try:
		with open(outFile, "w") as f:
			f.write(html)
	except:
		error("error writing to the html file")
		sys.exit(1)

	try:
		source_directory = os.path.join(main_directory, "Ubuntu_Mono")
		destination_directory= os.path.abspath(os.path.join("fonts", "Ubuntu_Mono"))
		copytree(source_directory, destination_directory, dirs_exist_ok=True)
	except:
		error("could not create directory for Ubuntu Mono font")

	if code_highlighting_needed:
		try:
			source_directory = os.path.join(main_directory, "highlight")
			destination_directory= os.path.abspath("highlight")
			copytree(source_directory, destination_directory, dirs_exist_ok=True)
		except:
			error("could not create directory for code highlighting")

main()