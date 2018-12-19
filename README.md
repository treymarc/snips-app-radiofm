- [Requirements](#Requirements)
- [AEC](#AEC)
- [Demo](#Demo)
- [Command-List](#Command-list)
- [Tips](#Tips)


[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/snipsco/snips-app-template-py/blob/master/LICENSE)

Control your rtl sdr dongle and listen to fm radio with snips

## Requirements

The app use `rtl_fm` to access the radio:

```bash
# install the rtl-sdr tool
sudo apt-get install rtl-sdr
```

The app must access the usb rtl_sdr dongle:

```
# grant access to the usb dongle and audio to the skill server
sudo usermod -a -G plugdev _snips-skills
```

If you use `pulseaudio` the app must have access to pulseaudio:

```
# grant access to the usb dongle and audio to the skill server
sudo usermod -a -G pulse-access _snips-skills
```

## AEC

for best result it is advised to setup the AEC module with pulseaudio:

```bash
#! /bin/bash
set -e

# Install PulseAudio
sudo apt-get update
sudo apt-get install -y --reinstall pulseaudio

# Comment the lines that overwrite the asound.conf
sudo sed -i.bak 's/^\(.*asound\.conf.*\)/# \1/' /usr/bin/seeed-voicecard

# redirect alsa traffic to pulseaudio through the pulse alsa module
sudo rm /etc/asound.conf || true
sudo tee /etc/asound.conf > /dev/null <<EOS
pcm.!default {
   type pulse
   fallback "sysdefault"
}
ctl.!default {
   type pulse
   fallback "sysdefault"
}
EOS

# Do NOT run pulseaudio in realtime mode as it will crash on loading echo cancellation
sudo tee /lib/systemd/system/pulseaudio.service > /dev/null <<EOS
[Unit]
Description=PulseAudio Daemon
[Install]
WantedBy=multi-user.target
[Service]
Type=simple
PrivateTmp=true
Environment=HOME=/tmp/pulseaudio
ExecStart=/usr/bin/pulseaudio -v --daemonize=no --system --realtime=no --log-target=journal
ExecStop=/usr/bin/pulseaudio -k
Restart=always
RestartSec=2
EOS

# Allow users access to pulseaudio on next login
sudo usermod -a -G pulse-access _snips
sudo usermod -a -G pulse-access pi

# Change default sample rate to something higher
sudo sed -i.bak 's/^;\?\s*default-sample-rate.*/default-sample-rate = 48000/' /etc/pulse/daemon.conf

# Add a script to enable the echo cancellation module once pulseaudio has loaded the soundcard
sudo tee /usr/local/bin/pulse-aec.sh > /dev/null <<'EOS'
#!/bin/bash
# name of the mic and speaker to use
mic="alsa_input.platform-soc_sound.analog-stereo"
speaker="alsa_output.platform-soc_sound.analog-stereo"
# wait for the source to exist
for (( ; ; ))
do
   sleep 1
   found=`pactl list sources | grep Name: | grep -v ".monitor" | grep ${mic} | wc -l `
   if [ "$found" == "1" ]
   then
        break
   fi
done
sleep 2
# load the echo-cancel module
pactl load-module \
    module-echo-cancel \
    source_master=${mic} \
    sink_master=${speaker} \
    aec_method=webrtc \
    use_master_format=1 \
    aec_args='"high_pass_filter=1 noise_suppression=0 analog_gain_control=0"'
EOS

# The script is owned by the pulseaudio system user
pulse_user=pulse
sudo chmod +x /usr/local/bin/pulse-aec.sh
sudo chown ${pulse_user}:${pulse_user} /usr/local/bin/pulse-aec.sh

# Add a service file to run the aec script before the audio server but after pulseaudio
sudo tee /lib/systemd/system/pulseaudio-aec.service > /dev/null <<EOS
[Unit]
Description=PulseAudio AEC Module
After=pulseaudio.service
[Install]
WantedBy=multi-user.target
[Service]
Type=simple
User=${pulse_user}
Group=${pulse_user}
ExecStart=/usr/local/bin/pulse-aec.sh
EOS

# Only run the audio server once echo cancellation is loaded
sudo tee /etc/systemd/system/multi-user.target.wants/snips-audio-server.service > /dev/null <<EOS
[Unit]
Description=Snips Audio Server
After=network.target pulseaudio.service pulseaudio-aec.service
[Service]
User=_snips
Group=_snips
ExecStart=/usr/bin/snips-audio-server
Restart=always
RestartSec=2
[Install]
WantedBy=multi-user.target
EOS

# change default sink and source
sudo sed -i.bak 's/^;\?\s*default-sink.*/default-sink = alsa_output.platform-soc_sound.analog-stereo.echo-cancel/' /etc/pulse/client.conf
sudo sed -i.bak 's/^;\?\s*default-source.*/default-source = alsa_input.platform-soc_sound.analog-stereo.echo-cancel/' /etc/pulse/client.conf

sudo systemctl enable pulseaudio.service
sudo systemctl enable pulseaudio-aec.service
sudo systemctl enable snips-audio-server.service

sudo reboot
```

## Demo

TODO

## Command-list

TOD

## Tips

you must stop the radio before stopping the skill.
