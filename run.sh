#!/bin/bash

#./run.sh -v ../vcfs/platinum/platinum-exome.vcf -p ../vcfs/platinum/platinum.ped -r /scratch/ucgd/lustre/common/data/Reference/GRCh37/human_g1k_v37_decoy_phix.fasta -g /scratch/ucgd/lustre-work/marth/u0691312/reference/slivar.gnomad.hg37.added.annotations.zip -d /scratch/ucgd/lustre/work/u0691312/reference/ensembl/ -u /scratch/ucgd/lustre/work/u0691312/reference/ensembl/Plugins/ -l /scratch/ucgd/lustre/work/u0691312/reference/ensembl/Plugins/revel_all_chromosomes_vep.tsv.gz

# /uufs/chpc.utah.edu/common/HIPAA/u0691312/scripts/vep_grch37.sh # here are some flags

#vep -i varbayes_tmpdir/slivar.tmp -o varbayes_tmpdir/slivar.tmp.vep.vcf --quiet --fork 40 --fields "Location,Allele,SYMBOL,IMPACT,Consequence,Protein_position,Amino_acids,Existing_variation,IND,ZYG,ExACpLI,REVEL,DOMAINS,CSN,PUBMED" --cache --dir_cache /scratch/ucgd/lustre/work/u0691312/reference/ensembl/ --dir_plugins /scratch/ucgd/lustre/work/u0691312/reference/ensembl/Plugins/ --assembly GRCh37 --port 3337 --force_overwrite --fasta /scratch/ucgd/lustre/common/data/Reference/GRCh37/human_g1k_v37_decoy_phix.fasta --symbol --biotype --vcf --domains --pubmed --no_stats --plugin ExACpLI --plugin CSN --plugin REVEL,/scratch/ucgd/lustre/work/u0691312/reference/ensembl/Plugins/revel_all_chromosomes_vep.tsv.gz;

helpMessage="Usage: VarBayes [OPTION]\n
\tDescription of VarBayes\n
\t\t-h, --help                Print help instructions\n
\t\t-v, --vcf_file            Input VCF File Path [REQUIRED]\n
\t\t-p, --ped_file            Input PED File Path [REQUIRED]\n
\t\t-r, --reference_file      Reference (FASTA) File Path [REQUIRED]\n
\t\t-c, --get_clinvar         Download latest ClinVar file [if no ClinVar file available in the data directory this arg will be ignored and ClinVar will be downloaded automatically reguardless]\n
\t\t-g, --gnomad              GNOMAD File Path [REQUIRED]\n
\t\t-d, --vep_cache_dir       VEP Cache Directory Path [REQUIRED]\n
\t\t-u, --vep_plugin_dir      VEP Plugin Directory Path [REQUIRED]\n
\t\t-l, --vep_revel_file      VEP REVEL File Path [REQUIRED]\n
\t\t-t, --gnomad_af_threshold gnomAD_AF threshold (default value = 0.01)\n
\t\t-j, --revel_af_threshold  REVEL threshold [Ask Matt] (default value = 0.6)\n
\t\t-y, --prior_probability   Prior probability [Optional, default 0.1]\n
\t\t-o, --odds_pathogenic     The odds of pathogenicity for 'Very Strong' [Optional, default 350]\n
\t\t-e, --exponent            The exponent that sets the strength of Supporting/Moderate/Strong compared to 'Very Strong' [Optional, default 0.1]\n
\t\t-f, --finished_vcf_path   File name of the output vcf [REQUIRED]\n"

PARAMS=""
while (( "$#" )); do
	case "$1" in
		-h|--help)
			echo -e $helpMessage
			exit 0
			;;
		-c|--get_clinvar)
			getClinVar=1
			shift 1
			;;
		-t|--gnomad_af_threshold)
			gnomadAFThreshold=$2
			shift 2
			;;
		-j|--revel_af_threshold)
			revelAFThreshold=$2
			shift 2
			;;
		-y|--prior_probability)
			priorProbability=$2
			shift 2
			;;
		-o|--odds_pathogenic)
			oddsPathogenic=$2
			shift 2
			;;
		-e|--exponent)
			exponent=$2
			shift 2
			;;
		-f|--finished_vcf_path)
			finishedVCFPath=$2
			shift 2
			;;
		-v|--vcf_file)
			vcfFile=$2
			shift 2
			;;
		-p|--ped_file)
			pedFile=$2
			shift 2
			;;
		-g|--gnomad)
			gnomadFile=$2
			shift 2
			;;
		-r|--reference_file)
			referenceFile=$2
			shift 2
			;;
		-d|--vep_cache_dir)
			vepCacheDir=$2
			shift 2
			;;
		-u|--vep_plugin_dir)
			vepPluginDir=$2
			shift 2
			;;
		-l|--vep_revel_file)
			vepRevelFile=$2
			shift 2
			;;
		--) # end argument parsing
			shift
			break
			;;
		-*|--*=) # unsupported flags
			echo "Error: Unsupported flag $1" >&2
			exit 1
			;;
		*) # preserve positional arguments
			PARAMS="$PARAMS $1"
			shift
			;;
	esac
done
if [[ -z $vcfFile || -z $pedFile || -z $gnomadFile || -z $referenceFile || -z $vepCacheDir || -z $gnomadFile || -z $vepRevelFile || -z $vepPluginDir || -z $finishedVCFPath ]]; then
	echo "Make Sure you provide out all required parameters"
	echo -e $helpMessage
	exit 0
fi
if [[ -z $gnomadAFThreshold ]]; then
	gnomadAFThreshold='0.01'
fi
if [ -z $revelAFThreshold ]; then
	revelAFThreshold='0.6'
fi
if [ -z $priorProbability ]; then
	priorProbability='0.1'
fi
if [ -z $oddsPathogenic ]; then
	oddsPathogenic='350'
fi
if [ -z $exponent ]; then
	exponent='2.0'
fi
tmpDirectory=data
if [ ! -d "$tmpDirectory" ]; then
	mkdir $tmpDirectory
fi
clinVarFile="$tmpDirectory/clinvar.grc37.vep.vcf.gz"
if [ $getClinVar -eq 1 ] || [ ! -f $clinVarFile ]; then
	wget -O data/clinvar.grc37.vcf.gz ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/clinvar.vcf.gz
	wget -O data/clinvar.grc37.vcf.gz.tbi ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/clinvar.vcf.gz.tbi
	vep -i data/clinvar.grc37.vcf.gz \
		-o data/clinvar.grc37.vep.vcf \
		--quiet \
		--fork 40 \
		--fields "Location,Allele,SYMBOL,IMPACT,Consequence,Protein_position,Amino_acids,Existing_variation,IND,ZYG,ExACpLI,REVEL,DOMAINS,CSN,PUBMED" \
		--cache \
		--dir_cache $vepCacheDir \
		--dir_plugins $vepPluginDir \
		--assembly GRCh37 \
		--port 3337 \
		--force_overwrite \
		--fasta $referenceFile \
		--symbol \
		--biotype \
		--vcf \
		--domains \
		--pubmed \
		--no_stats \
		--plugin ExACpLI \
		--plugin CSN \
		--plugin REVEL,$vepRevelFile;
	bgzip -f data/clinvar.grc37.vep.vcf
	tabix -f $clinVarFile
fi
tmpFile=$tmpDirectory/slivar.tmp
externals/slivar/slivar expr \
	--vcf $vcfFile \
	--ped $pedFile \
	--gnotate $gnomadFile \
	--out-vcf $tmpDirectory/slivar.tmp;

vep -i $tmpDirectory/slivar.tmp \
	-o $tmpDirectory/slivar.tmp.vep.vcf \
    --quiet \
	--fork 40 \
	--fields "Location,Allele,SYMBOL,IMPACT,Consequence,Protein_position,Amino_acids,Existing_variation,IND,ZYG,ExACpLI,REVEL,DOMAINS,CSN,PUBMED" \
	--cache \
	--dir_cache $vepCacheDir \
	--dir_plugins $vepPluginDir \
	--assembly GRCh37 \
	--port 3337 \
	--force_overwrite \
	--fasta $referenceFile \
	--symbol \
	--biotype \
	--vcf \
	--domains \
	--pubmed \
	--no_stats \
	--plugin ExACpLI \
	--plugin CSN \
	--plugin REVEL,$vepRevelFile;
bgzip -f $tmpDirectory/slivar.tmp.vep.vcf
tabix -f $tmpDirectory/slivar.tmp.vep.vcf.gz
echo "python VarBayes.py -v $tmpDirectory/slivar.tmp.vep.vcf.gz -f $pedFile -d $finishedVCFPath -c $clinVarFile -e $exponent -o $oddsPathogenic -p $priorProbability -a $gnomadAFThreshold -r $revelAFThreshold"
python VarBayes.py -v $tmpDirectory/slivar.tmp.vep.vcf.gz -f $pedFile -d $finishedVCFPath -c $clinVarFile -e $exponent -o $oddsPathogenic -p $priorProbability -a $gnomadAFThreshold -r $revelAFThreshold