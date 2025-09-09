dirname=$(dirname $(dirname $(readlink -f $0)))
tree $dirname -I dist -I __pycache__ -I dist -I build -I *.egg-info -I config -I data -I *.log > $dirname/package_structure.txt
sed -i "s#$dirname#ftp_transfer#g" $dirname/package_structure.txt > $dirname/ftp_transfer_files.txt
python $dirname/setup.py bdist_wheel --dist-dir $dirname/dist
