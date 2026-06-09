import pathlib
import npyscreen
from .common import get_html_from_search, clear, get_megakino_episodes, get_title
from megakino.src.actions.download import download
from megakino.src.extractors.megakino import megakino_get_direct_link
from megakino.src.extractors.voe import voe_get_direct_link
from megakino.src.actions.syncplay import syncplay
from megakino.src.actions.watch import watch
from megakino.src.parser import args as _args


def main():
    HTML_CONTENTS = []
    while True:
        results = get_html_from_search()
        HTML_CONTENTS.extend(results)
        if not results:
            if not HTML_CONTENTS:
                answer = input("Keine Ergebnisse. Erneut suchen? (j/n): ").strip().lower()
                if answer == 'j':
                    continue
                return
            break
        answer = input("Weitere Suche hinzufügen? (j/n): ").strip().lower()
        if answer != 'j':
            break

    episodes = {}
    for soup in HTML_CONTENTS:
        episodes.update(get_title(soup))
    titles = list(episodes.keys())

    class MegakinoForm(npyscreen.ActionForm):
        def create(self):
            self.action = self.add(npyscreen.TitleSelectOne, name="Action:", max_height=6, values=["Watch", "Download", "Syncplay"], scroll_exit=True, value=1)

            self.provider = self.add(npyscreen.TitleSelectOne, name="Provider:", max_height=5, values=["Megakino", "VOE"], scroll_exit=True, value=0)

            self.download_path = self.add(npyscreen.TitleFilenameCombo, name="Download-Pfad:", value=str(_args.path))

            self.episodes = self.add(npyscreen.TitleMultiSelect, name="Choose Episodes:", values=[">>> Select all <<<"] + titles, scroll_exit=True)
            self._select_all_active = False
            self.episodes.entry_widget.when_value_edited = self._handle_select_all

        def _handle_select_all(self):
            current = list(self.episodes.value or [])
            select_all_now = 0 in current
            all_indices = list(range(len(titles) + 1))
            if select_all_now and not self._select_all_active:
                self.episodes.value = all_indices
                self._select_all_active = True
            elif not select_all_now and self._select_all_active:
                self.episodes.value = []
                self._select_all_active = False
            else:
                self._select_all_active = select_all_now
            self.episodes.display()

        def on_ok(self):
            selected_action = self.action.get_selected_objects()
            selected_provider = self.provider.get_selected_objects()
            selected_episodes = self.episodes.get_selected_objects()


            all_marker = ">>> Select all <<<"
            if all_marker in selected_episodes:
                chosen_episodes = titles
            else:
                chosen_episodes = [e for e in selected_episodes if e != all_marker]
            selected_action = selected_action[0]
            selected_provider = selected_provider[0]
            selected_path = self.download_path.value or str(_args.path)
            clear()

            direct_links = []
            if selected_provider == "Megakino":
                for soup in HTML_CONTENTS:
                    megakino_list = get_megakino_episodes(soup)
                    if megakino_list:
                        for episode in megakino_list:
                            link = megakino_get_direct_link(episode)
                            direct_links.append(link)

            if selected_provider == "VOE" or not direct_links:
                direct_links = []
                urls = [episodes[name] for name in chosen_episodes]
                if urls:
                    for episode in urls:
                        link = voe_get_direct_link(episode)
                        direct_links.append(link)
            print(direct_links)
            if selected_action == "Watch":
                watch(direct_links, chosen_episodes)
            elif selected_action == "Download":
                download(direct_links, chosen_episodes, selected_path)
            elif selected_action == "Syncplay":
                syncplay(direct_links, chosen_episodes)

            self.parentApp.switchForm(None)

        def on_cancel(self):
            exit()

    class MegakinoApp(npyscreen.NPSAppManaged):
        def onStart(self):
            self.form = self.addForm("MAIN", MegakinoForm, name="Megakino-Downloader")


    app = MegakinoApp()
    app.run()


if __name__ == "__main__":
    main()
