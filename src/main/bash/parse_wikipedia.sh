#!/usr/bin/env bash
# This script is responsible for processing Wikipedia articles generated
# by WikiExtractor and parse them with a dependency parser.
# For each input file (featuring multiple articles), it generates one file
# containing one json object per line. Each json object contains of a paragraph
# from the input text. 


N_THREADS=12

function annotate() {
    local input_path=$1
    local annotation_dir=$2

    mkdir -p ${annotation_dir}

    # Annotate articles.
    echo "[1/3] Annotating articles"
    find ${input_path} -type f -printf "%p %P\n" | \
        parallel --gnu -j ${N_THREADS} --colsep ' ' '
        	in_file_chunk={1}
        	out_file_chunk='${annotation_dir}'/$(echo {2} | sed s/"\/"/_/)
        	temp_out_file_chunk=${out_file_chunk}.tmp
        	report_file_chunk=${out_file_chunk}.report
        	echo $in_file_chunk $out_file_chunk $temp_out_file_chunk $report_file_chunk
        	if [ -f "$out_file_chunk" ]; then
        		print "Output file $out_file_chunk already exists. Skipping."
        	else
        		bunzip2 -c ${in_file_chunk} | python '$(pwd)'/src/main/python/parasub/preprocessing/dependency_parse_wikipedia.py 2>${report_file_chunk} | bzip2 > ${temp_out_file_chunk}
        		mv ${temp_out_file_chunk} ${out_file_chunk}
        	fi

		'
}

input_path=$1
annotation_dir=$2

if [[ -z ${input_path} ]] || [[ -z ${annotation_dir} ]] ; then
    echo "Insert base directory of extracted wikipedia files as first argument, output directory as second argument."
    exit 1
fi

annotate ${input_path} ${annotation_dir}
