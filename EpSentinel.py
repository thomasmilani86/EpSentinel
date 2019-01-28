from EpConf import *
from EpSource import *
import requests

print("Checking for TV shows episodes missing on your computer")

# Get the list of TVshows available on Kodi DB
showlist = get_tvseries(db_path)

# POST request for TVdb API token
url = "https://api.thetvdb.com/login"
payload = {"apikey": "439DFEBA9D3059C6"}
r = requests.post(url, json=payload)
token = r.json()['token']

html_missing = []
list_next = []

show_qty = len(showlist)
show_num = 1


for show in showlist:
    print("{name} ({show_num}/{len})".format(name=show.name, show_num=show_num, len=show_qty))

    # Scrap TheTVdb
    web_eplist, next_ep_num, next_ep_date = show.webscrap(token)

    # Include in html table for next episodes
    list_next.append((show.name, next_ep_num, next_ep_date))

    # Look for missing episodes in Kodi DB with regards to TheTVdb.com
    missing_ep = show.missing_ep(db_path, web_eplist)
    print(str(len(missing_ep))+" episodes missing")

    # Produce HTML table for episodes missing if any
    if len(missing_ep) > 0:
        html = new_show(show.name, len(missing_ep))

        # Scrap links on ThePirateBay.com
        for ep in missing_ep:
            href = look_tpb(show.name, ep, tpb, number_links)
            html += insert(str(ep[0]), href)

        html += close_show()

        html_missing.append((html, len(missing_ep)))

    print("")
    show_num += 1

# Sort the TVshows by number of missing episodes
html_missing.sort(key=lambda tup: tup[1])
# Filter next episodes available
list_next = [ep for ep in list_next if ep[1] != 0]
# Sort the future episodes by next coming
list_next.sort(key=lambda tup: tup[2])

# Open HTML output
output = HtmlSummary(out_path)

# Dump missing episodes in HTML file
for html in html_missing:
    output.dump_html(html[0])

# Add necessary HTML tags between the 2 tables
output.open_table_next()

# Dump next episodes table in HTML file
with open(output.path, 'a') as f:
    for next_ep in list_next:
        html = insert_next(next_ep)
        f.write(html)

output.close()
