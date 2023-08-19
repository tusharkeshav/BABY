sudo apt install python-tk python3 sox asla-utils
voice2json --profile en-us_kaldi-zamia download-profile # thsi will download file in $HOME/.local/share/voice2json/en-us_kaldi-zamia
path=$(pwd)
rm $HOME/.local/share/voice2json/en-us_kaldi-zamia/sentences.ini
ln -s $p ath/sentences.ini $HOME/.local/share/voice2json/en-us_kaldi-zamia/sentences.ini
voice2json train-profile
APPDIR='/usr/bin/baby'
${APPDIR}/venv/bin/python -m pip install -r requirements.txt