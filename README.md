# Daddy
To develop
- roll a dice
- heads tail
- 

dependency:
portaudio19-dev




'{"text": "set brightness to two", "likelihood": 0.20411500000000005, "transcribe_seconds": 0.6375299059982353, "wav_seconds": 6.176, "tokens": [{"token": "set", "start_time": 0.0, "end_time": 4.95, "likelihood": 1.0}, {"token": "brightness", "start_time": 4.95, "end_time": 5.69921, "likelihood": 0.993665}, {"token": "to", "start_time": 5.69921, "end_time": 5.70049, "likelihood": 0.988279}, {"token": "two", "start_time": 5.70088, "end_time": 5.91103, "likelihood": 0.222886}], "timeout": false}', 'Ready']
>>> y[2]
'LOG (online2-cli-nnet3-decode-faster-confidence[5.5]:ComputeDerivedVars():ivector-extractor.cc:204) Done.'
>>> y[3]
'LOG (online2-cli-nnet3-decode-faster-confidence[5.5]:RemoveOrphanNodes():nnet-nnet.cc:948) Removed 1 orphan nodes.'
>>> y[7]
'{"text": "set brightness to two", "likelihood": 0.20411500000000005, "transcribe_seconds": 0.6375299059982353, "wav_seconds": 6.176, "tokens": [{"token": "set", "start_time": 0.0, "end_time": 4.95, "likelihood": 1.0}, {"token": "brightness", "start_time": 4.95, "end_time": 5.69921, "likelihood": 0.993665}, {"token": "to", "start_time": 5.69921, "end_time": 5.70049, "likelihood": 0.988279}, {"token": "two", "start_time": 5.70088, "end_time": 5.91103, "likelihood": 0.222886}], "timeout": false}'
>>> 


voice2json record-command \
    --audio-source <(sox turn-on-the-living-room-lamp.wav -t raw -) \
    --wav-sink /dev/null

For the TTS:
We need festival app(below are command of binary and voice binary)
    sudo apt-get install festival
    sudo apt-get install festvox-us-slt-hts
    festival -i
    festival> (voice_cmu_us_slt_arctic_hts) 
    festival> (SayText "Don't hate me, I'm just doing my job!")
    
    You can do it from the command line by using -b (or --batch) and putting each command into single quotes:
    
    festival -b '(voice_cmu_us_slt_arctic_hts)' \
        '(SayText "The temperature is 22 degrees centigrade and there is a slight breeze from the west.")'
