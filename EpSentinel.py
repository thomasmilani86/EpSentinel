from EpConf import *
from EpSource import *

print("Checking for TV shows episodes missing on your computer")

# Get the list of TVshows availabl on Kodi DB
showlist = get_tvseries(db_path)
output = HtmlSummary(out_path)

for show in showlist:
    print(show.name)

    # Find the missing episodes in Kodi DB with regards to TheTVdb.com
    missing_ep = show.missing_ep(db_path)
    print(str(len(missing_ep))+" episodes missing")

    # Print episodes missing if any
    if len(missing_ep) > 0:
        print(missing_ep)
        output.new_show(show.name)

        # Scrap links on ThePirateBay.com
        for ep in missing_ep:
            href_error = look_tpb(show.name, ep, tpb, number_links)
            output.insert(str(ep[0]), href_error)

        output.close_show()

    print("")

output.close()
