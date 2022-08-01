# Japanese Duolingo Visualizer

Visualize your 日本語 progress in Duolingo everyday. Powered with Python, Poetry, GitHub Actions, and GitHub Pages (HTML, CSS, JS, Bootstrap).

## Motivation

Everyday, I practice 日本語 on Duolingo.

One feature that I find the lack of it disturbing in Duolingo is a feature to visualize a graph/plot to trace your language learning progression. As with other skills, language requires you to constantly train and practice everyday to ensure that your skills are always at the bleeding edge. Essentially, by having that feature, we could trace our language learning progression everyday, which I believe is good for several reasons. Gaining a constant amount of Duolingo's experience points everyday would allow you to give an idea about how continuous your learning progression is. We trace three points in this tool: experience, streak information, and number of words learned during the usage of the application. All of these will be plotted to a chart to help you visualize your progress.

Mainly, this project is inspired by:

- [Satella](https://github.com/lauslim12/Satella)
- [Freedomofkeima's GitHub Profile Visualizer](https://github.com/freedomofkeima/github-profile-visualizer)
- [Kartik Talwar's Unofficial Duolingo API](https://github.com/KartikTalwar/Duolingo)

Thank you for the inspiration!

## Usage (Automatic)

This right and recommended usage of this is 'you should never have to run this script manually, except in some rare circumstances'. The way to use this repository is as follows:

- Fork this repository!
- Log in to your Duolingo account in your web browser.
- Get your JWT (I assume you're using Google Chrome) from `Inspect` -> `Application` -> `Cookies` -> Copy the `jwt_token` entry.
- Put several secrets in the repository (`Settings` -> `Secrets` -> `Actions`): `DUOLINGO_USERNAME`, `DUOLINGO_PASSWORD`, `DUOLINGO_JWT`.
- You have to use your real credentials, or else the API will not let you in. Feel free to check the source code if you supect anything!
- Put more secrets: `GIT_AUTHOR_EMAIL`, and `GIT_AUTHOR_NAME` (equivalent when you're setting up Git: `git config --global user.email ...`).
- For the first time, you should clear the `data/duolingo-progress.json` file manually, leaving only `[]` (an empty array) in that file.
- Wait for the cron, and then the script will run properly without you having to do anything! Please check the repository to see the update.

## Usage (Manual)

This should be dedicated for GitHub Actions only. If you want the script manually, then:

```bash
# Clone repository.
git clone git@github.com:lauslim12/japanese-duolingo-visualizer.git
cd japanese-duolingo-visualizer

# Use `poetry`.
poetry shell
poetry install

# Put necessary environment variables, or else it will not work.
export DUOLINGO_USERNAME=...
export DUOLINGO_PASSWORD=...
export DUOLINGO_JWT=...

# Run script.
poetry run python3 main.py
```

## Notes

Ensure to run these scripts to keep the code quality consistent:

```bash
poetry run black src main.py
poetry run isort src main.py
poetry run mypy src main.py
```

## License

MIT License.
