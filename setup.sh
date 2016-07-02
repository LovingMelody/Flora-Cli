#! /bin/bash
echo "Setting Up Flora-Cli"
#/usr/bin/mkdir /usr/local/bin/Fuzzy
#/usr/bin/mkdir /usr/local/bin/Fuzzy/Flora-cli/
cp /Flora-Cli/main.py /usr/local/bin/flora-cli
chmod +x /usr/local/bin/flora-cli
echo "Done"
flora-cli
