import requests
from bs4 import BeautifulSoup
import curses
from .common import BASE_URL

MAX_PAGES = 5


def _relevance_score(title: str, keyword: str) -> int:
    t = title.lower()
    k = keyword.lower()
    if t == k:
        return 0
    if t.startswith(k):
        return 1
    words = t.split()
    if k in words:
        return 2
    if k in t:
        return 3
    return 4


def search_for_movie():
    print("Welcome to Megakino-Downloader!")
    keyword = input("What movie/series do you want to watch/download today? ")

    session = requests.Session()
    try:
        session.get(f"{BASE_URL}/index.php?yg=token", timeout=15)
    except requests.RequestException as e:
        print(f"Error: Unable to connect. Details: {e}")
        return []

    titles_links = []
    seen_urls = set()

    for page in range(MAX_PAGES):
        result_from = page * 20 + 1
        url = (
            f"{BASE_URL}/index.php?do=search&subaction=search"
            f"&search_start={page * 2}&full_search=0"
            f"&result_from={result_from}&story={keyword}"
        )
        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException:
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        page_results = []
        for link in soup.find_all('a', class_='poster'):
            title = link.find('h3', class_='poster__title')
            href = BASE_URL + link['href']
            if title and href not in seen_urls:
                seen_urls.add(href)
                page_results.append((title.text.strip(), href))

        if not page_results:
            break
        titles_links.extend(page_results)

    if not titles_links:
        msg = f"No results found for '{keyword}'."
        raise ValueError(msg)

    titles_links.sort(key=lambda x: _relevance_score(x[0], keyword))

    def curses_menu(stdscr, titles_links):
        curses.curs_set(0)
        current_row = 0
        offset = 0
        selected = set()

        while True:
            try:
                max_y, max_x = stdscr.getmaxyx()
                # 2 header lines + 1 footer line
                visible = max_y - 3

                if visible < 1:
                    raise ValueError("Please increase terminal size!")

                # Keep offset so current_row is always visible
                if current_row < offset:
                    offset = current_row
                elif current_row >= offset + visible:
                    offset = current_row - visible + 1

                stdscr.clear()

                header = f"Results (SPACE=select, ENTER=confirm, ESC=cancel) [{len(selected)} selected]:"
                stdscr.addstr(0, 0, header[:max_x - 1], curses.A_BOLD)

                for row_idx in range(visible):
                    item_idx = offset + row_idx
                    if item_idx >= len(titles_links):
                        break
                    title, _ = titles_links[item_idx]
                    prefix = "[x] " if item_idx in selected else "[ ] "
                    display = (prefix + title).encode("utf-8")[:max_x - 1]
                    if item_idx == current_row:
                        stdscr.addstr(row_idx + 2, 0, display, curses.color_pair(1))
                    else:
                        stdscr.addstr(row_idx + 2, 0, display)

                footer = f"Zeige {offset + 1}-{min(offset + visible, len(titles_links))} von {len(titles_links)}"
                stdscr.addstr(max_y - 1, 0, footer[:max_x - 1], curses.A_DIM)

                stdscr.refresh()

                key = stdscr.getch()

                if key == curses.KEY_UP and current_row > 0:
                    current_row -= 1
                elif key == curses.KEY_DOWN and current_row < len(titles_links) - 1:
                    current_row += 1
                elif key == curses.KEY_PPAGE:  # Page Up
                    current_row = max(0, current_row - visible)
                elif key == curses.KEY_NPAGE:  # Page Down
                    current_row = min(len(titles_links) - 1, current_row + visible)
                elif key == ord(' '):
                    if current_row in selected:
                        selected.discard(current_row)
                    else:
                        selected.add(current_row)
                elif key == curses.KEY_ENTER or key in [10, 13]:
                    if selected:
                        return [titles_links[i][1] for i in sorted(selected)]
                    else:
                        return [titles_links[current_row][1]]
                elif key == 27:
                    return []
            except ValueError:
                raise
            except Exception:
                raise ValueError("Please increase terminal size!")

    def main(stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        return curses_menu(stdscr, titles_links)

    selected_links = curses.wrapper(main)
    return selected_links


if __name__ == "__main__":
    movie_links = search_for_movie()
    if movie_links:
        for link in movie_links:
            print(f"Selected Link: {link}")
    else:
        print("No movie selected or an error occurred.")
