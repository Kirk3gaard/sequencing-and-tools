"""Source of truth for the catalogue. Edit here, run to regenerate data/*.json.
platforms: ont, hifi, sr (short-read: Illumina, Element, MGI/DNBSEQ, Ultima, SBX)
"""
import json, os

STEPS = [
 ("acq", "Acquisition & signal", "Run control, raw signal formats, adaptive sampling"),
 ("basecall", "Basecalling", "Signal or image to bases, plus modified bases"),
 ("trim", "Demux, adapters & artefacts", "Barcodes, adapters, chimeras, duplex pairs — the step most often skipped"),
 ("qc", "Read QC & filtering", "Length/quality summaries, filtering, subsampling"),
 ("correct", "Read correction", "Error correction of reads before assembly"),
 ("map", "Read mapping", "Aligning reads to references or assemblies"),
 ("profile", "Read-based profiling", "Taxonomic classification and abundance from reads"),
 ("assemble", "Assembly", "Metagenome and isolate assembly, plasmids, circularisation"),
 ("polish", "Polishing", "Consensus correction of assemblies"),
 ("bin", "Binning", "Grouping contigs into MAGs"),
 ("magqc", "MAG QC & dereplication", "Completeness, contamination, chimerism, ANI clustering"),
 ("taxonomy", "Genome taxonomy", "Placing genomes and MAGs in a taxonomy"),
 ("annotate", "Annotation", "Genes, function, BGCs, AMR, mobile elements, viruses"),
 ("methyl", "Methylation & epigenetics", "Modified-base pileups, motifs, methylation-aware binning"),
 ("variants", "Variants & strains", "SNVs, SVs, strain haplotypes"),
 ("coverage", "Coverage & sketching", "Abundance, depth, k-mer sketches, ANI"),
 ("workflow", "Workflows", "End-to-end pipelines and workflow engines"),
 ("viz", "Visualisation", "Graphs, alignments, MAG exploration"),
]

# (id, name, step, platforms, repo or None, bioconda or None, url or None, description, note, flags)
# flags: "artefact" = handles a commonly missed read artefact; "legacy" = superseded, listed for orientation
T = [
 # acquisition
 ("minknow","MinKNOW","acq",["ont"],None,None,"https://nanoporetech.com/software/devices/minknow","ONT instrument control software; writes POD5 and runs live basecalling.","Version is set per device; check the Software Release Notes before a big run.",[]),
 ("pod5","pod5","acq",["ont"],"nanoporetech/pod5-file-format","pod5",None,"Reference library and CLI for ONT's POD5 raw-signal format.","Use for merging/subsetting raw data before re-basecalling.",[]),
 ("slow5tools","slow5tools","acq",["ont"],"hasindu2008/slow5tools","slow5tools",None,"Convert, index and subset raw signal in the open SLOW5/BLOW5 format.","Compact archival alternative to POD5.",[]),
 ("readfish","readfish","acq",["ont"],"LooseLab/readfish",None,None,"Adaptive sampling (read-until) with custom targets and logic.","For depletion/enrichment beyond the MinKNOW built-in.",[]),
 ("bclconvert","BCL Convert / DRAGEN","acq",["sr"],None,None,"https://support.illumina.com/sequencing/sequencing_software/bcl-convert.html","Illumina BCL to FASTQ conversion and demultiplexing.","Proprietary; adapter trimming optional in sample sheet.",[]),
 ("bases2fastq","bases2fastq","acq",["sr"],None,None,"https://docs.elembio.io/docs/bases2fastq/","Element AVITI base-file to FASTQ conversion and demultiplexing.","Proprietary.",[]),
 # basecalling
 ("dorado","Dorado","basecall",["ont"],"nanoporetech/dorado",None,None,"ONT's production basecaller: simplex, duplex, modified bases, demux, trim, correct, polish.","Model choice (fast/hac/sup, version) changes accuracy and artefacts — record it per dataset.",[]),
 ("bonito","Bonito","basecall",["ont"],"nanoporetech/bonito",None,None,"ONT research basecaller for training custom models.","Use only to train or test models; Dorado for production.",[]),
 ("remora","Remora","basecall",["ont"],"nanoporetech/remora",None,None,"Training framework for modified-base models used by Dorado.","Custom mod models, e.g. new bacterial motifs.",[]),
 ("smrtlink","SMRT Link / on-instrument HiFi","basecall",["hifi"],None,None,"https://www.pacb.com/support/software-downloads/","PacBio's on-instrument consensus (HiFi) and kinetics-based base modification calling.","Revio/Vega output HiFi BAM with 5mC (and 6mA) tags directly.",[]),
 ("guppy","Guppy","basecall",["ont"],None,None,"https://nanoporetech.com","Former ONT basecaller.","Superseded by Dorado; R9 data only.",["legacy"]),
 # trim / artefacts
 ("dorado_trim","Dorado demux / trim","trim",["ont"],"nanoporetech/dorado",None,None,"Barcode classification and adapter/primer trimming inside Dorado.","Trims read ends only — internal adapters and chimeras survive.",["artefact"]),
 ("porechop_abi","Porechop_ABI","trim",["ont"],"bonsai-team/Porechop_ABI","porechop_abi",None,"Infers adapter sequences from the reads themselves and trims ends and middles.","Catches unknown/kit-mismatched adapters and splits reads with middle adapters.",["artefact"]),
 ("porechop","Porechop","trim",["ont"],"rrwick/Porechop","porechop",None,"Original ONT adapter trimmer with known-adapter database.","Unmaintained since 2018; use Porechop_ABI.",["artefact","legacy"]),
 ("duplex_tools","duplex-tools","trim",["ont"],"nanoporetech/duplex-tools",None,None,"Finds duplex pairs and splits reads at internal adapters (split_on_adapter).","Removes concatenated/chimeric reads that inflate N50 and cause misassemblies.",["artefact"]),
 ("yacrd","yacrd","trim",["ont","hifi"],"natir/yacrd","yacrd",None,"Detects and removes chimeric and low-coverage regions via all-vs-all overlaps.","Chimera screen before assembly.",["artefact"]),
 ("pychopper","Pychopper","trim",["ont"],"epi2me-labs/pychopper","pychopper",None,"Identifies, orients and trims full-length cDNA reads.","Transcriptomics only.",["artefact"]),
 ("barbell","Barbell","trim",["ont"],"rickbeeloo/barbell","barbell",None,"Fast, pattern-aware nanopore demultiplexer that classifies barcode/adapter layouts per read.","Flags concatenated and mis-ligated barcode reads that standard demux keeps; compare against Dorado demux.",["artefact"]),
 ("lima","lima","trim",["hifi"],None,"lima","https://lima.how","PacBio barcode demultiplexing and primer removal.","Standard HiFi demultiplexer.",["artefact"]),
 ("skera","skera","trim",["hifi"],None,"pbskera","https://skera.how","Splits Kinnex/MAS-Seq concatenated arrays into segmented reads.","Required for Kinnex 16S and RNA.",["artefact"]),
 ("hifiadapterfilt","HiFiAdapterFilt","trim",["hifi"],"sheinasim/HiFiAdapterFilt","hifiadapterfilt",None,"Removes HiFi reads containing residual adapter sequence.","Residual adapters still occur in HiFi and break assemblies.",["artefact"]),
 ("cutadapt","cutadapt","trim",["sr","ont","hifi"],"marcelm/cutadapt","cutadapt",None,"General adapter/primer trimming and demultiplexing.","Amplicon primer removal on any platform.",["artefact"]),
 ("fastp","fastp","trim",["sr"],"OpenGene/fastp","fastp",None,"All-in-one short-read trimming, filtering and QC report.","Default first step for Illumina/Element/MGI reads.",["artefact"]),
 ("bbduk","BBDuk (BBTools)","trim",["sr"],None,"bbmap","https://sourceforge.net/projects/bbmap/","k-mer based adapter, contaminant and phiX removal.","Fast decontamination of short reads.",["artefact"]),
 # qc
 ("nanoplot","NanoPlot","qc",["ont","hifi"],"wdecoster/NanoPlot","nanoplot",None,"Length/quality plots and stats for long reads.","Quick per-run summary.",[]),
 ("nanocomp","NanoComp","qc",["ont","hifi"],"wdecoster/nanocomp","nanocomp",None,"Compare several long-read datasets side by side.","",[]),
 ("cramino","cramino","qc",["ont","hifi"],"wdecoster/cramino","cramino",None,"Very fast summary stats from BAM/CRAM.","Stats straight from unaligned Dorado BAMs.",[]),
 ("chopper","chopper","qc",["ont","hifi"],"wdecoster/chopper","chopper",None,"Rust filter/trimmer for long reads by quality, length and contaminants.","Replaces NanoFilt.",[]),
 ("deacon","deacon","qc",["ont","hifi","sr"],"bede/deacon","deacon",None,"Fast alignment-free minimizer filter for host/contaminant depletion of reads.","Index choice decides what is removed; keep the depleted fraction for audit.",[]),
 ("filtlong","Filtlong","qc",["ont"],"rrwick/Filtlong","filtlong",None,"Keeps the best reads by length and quality, optionally guided by short reads.","Subset for isolate assembly.",[]),
 ("fastplong","fastplong","qc",["ont","hifi"],"OpenGene/fastplong","fastplong",None,"fastp for long reads: adapter trimming, filtering, report.","",["artefact"]),
 ("seqkit","SeqKit","qc",["ont","hifi","sr"],"shenwei356/seqkit","seqkit",None,"Swiss-army knife for FASTA/Q manipulation and stats.","",[]),
 ("rasusa","Rasusa","qc",["ont","hifi","sr"],"mbhall88/rasusa","rasusa",None,"Random subsampling to a target depth or base count.","Fair comparisons across datasets.",[]),
 ("fastqc","FastQC","qc",["sr"],"s-andrews/FastQC","fastqc",None,"Classic short-read QC report.","",[]),
 ("multiqc","MultiQC","qc",["ont","hifi","sr"],"MultiQC/MultiQC","multiqc",None,"Aggregates QC outputs from many tools into one report.","",[]),
 # correct
 ("dorado_correct","Dorado correct (HERRO)","correct",["ont"],"nanoporetech/dorado",None,None,"Haplotype-aware read correction of ONT reads (HERRO model).","Built for single genomes; check strain collapse in metagenomes.",[]),
 ("herro","HERRO","correct",["ont"],"lbcb-sci/herro",None,None,"Deep-learning haplotype-aware read correction (standalone).","",[]),
 ("canu_correct","Canu (correction)","correct",["ont","hifi"],"marbl/canu","canu",None,"Overlap-based correction and trimming, also a full assembler.","Slow; mostly superseded by HERRO for ONT.",[]),
 # map
 ("minimap2","minimap2","map",["ont","hifi","sr"],"lh3/minimap2","minimap2",None,"De facto long-read aligner; also spliced and assembly alignment.","Pick the preset matching chemistry (lr:hq for R10 SUP).",[]),
 ("pbmm2","pbmm2","map",["hifi"],"PacificBiosciences/pbmm2","pbmm2",None,"minimap2 wrapper for PacBio BAMs keeping kinetics/tags.","",[]),
 ("winnowmap","Winnowmap2","map",["ont","hifi"],"marbl/Winnowmap","winnowmap",None,"minimap2 variant robust in repeats.","",[]),
 ("bwamem2","BWA-MEM2","map",["sr"],"bwa-mem2/bwa-mem2","bwa-mem2",None,"Fast BWA-MEM reimplementation for short reads.","",[]),
 ("bowtie2","Bowtie 2","map",["sr"],"BenLangmead/bowtie2","bowtie2",None,"Short-read aligner, common in binning coverage steps.","",[]),
 ("strobealign","strobealign","map",["sr"],"ksahlin/strobealign","strobealign",None,"Very fast short-read aligner; has an abundance mode for binning.","--aemb gives coverage for binning without BAMs.",[]),
 ("samtools","samtools / HTSlib","map",["ont","hifi","sr"],"samtools/samtools","samtools",None,"SAM/BAM/CRAM manipulation.","",[]),
 # profile
 ("kraken2","Kraken 2","profile",["ont","hifi","sr"],"DerrickWood/kraken2","kraken2",None,"k-mer read classifier.","Database choice dominates results; false positives at low abundance.",[]),
 ("bracken","Bracken","profile",["ont","hifi","sr"],"jenniferlu717/Bracken","bracken",None,"Re-estimates abundances from Kraken output.","",[]),
 ("centrifuger","Centrifuger","profile",["ont","hifi","sr"],"mourisl/centrifuger","centrifuger",None,"Memory-efficient read classifier (compressed index).","",[]),
 ("sylph","sylph","profile",["ont","hifi","sr"],"bluenote-1577/sylph","sylph",None,"Fast ANI-based species profiling against GTDB and others.","Strong default for profiling against GTDB.",[]),
 ("metabuli","Metabuli","profile",["ont","hifi","sr"],"steineggerlab/Metabuli","metabuli",None,"Classification using DNA and amino-acid k-mers jointly.","",[]),
 ("emu","Emu","profile",["ont","hifi"],"treangenlab/emu","emu",None,"Full-length 16S abundance estimation by EM.","For long-read 16S amplicons.",[]),
 ("metaphlan","MetaPhlAn 4","profile",["sr"],"biobakery/MetaPhlAn","metaphlan",None,"Marker-gene profiler.","Short-read oriented; human-gut biased database.",[]),
 ("motus","mOTUs","profile",["sr","ont"],"motu-tool/mOTUs","motus",None,"Marker-gene profiler including unknown species.","",[]),
 ("melon","Melon","profile",["ont","hifi"],"xinehc/melon","melon",None,"Long-read marker-gene profiling with genome-copy estimates.","",[]),
 ("ganon","ganon","profile",["ont","hifi","sr"],"pirovc/ganon","ganon",None,"Classification and profiling with easy custom/NCBI databases.","",[]),
 # assemble
 ("metaflye","metaFlye (Flye)","assemble",["ont","hifi"],"mikolmogorov/Flye","flye",None,"Repeat-graph assembler with metagenome mode.","Long-time long-read metagenome default.",[]),
 ("myloasm","myloasm","assemble",["ont","hifi"],"bluenote-1577/myloasm","myloasm",None,"Strain-resolving metagenome assembler for R10 and HiFi.","New; worth benchmarking against metaFlye.",[]),
 ("metamdbg","metaMDBG","assemble",["ont","hifi"],"GaetanBenoitDev/metaMDBG","metamdbg",None,"Minimizer de Bruijn graph metagenome assembler.","Fast, low memory; ONT support since v1.",[]),
 ("hifiasm","hifiasm","assemble",["hifi","ont"],"chhylp123/hifiasm","hifiasm",None,"Haplotype-resolved assembler; ONT simplex (--ont) supported.","Isolates and eukaryotes.",[]),
 ("hifiasm_meta","hifiasm-meta","assemble",["hifi"],"xfengnefx/hifiasm-meta","hifiasm_meta",None,"Metagenome mode of hifiasm for HiFi.","",[]),
 ("autocycler","Autocycler","assemble",["ont"],"rrwick/Autocycler","autocycler",None,"Automated consensus of multiple long-read isolate assemblies.","Successor to Trycycler.",[]),
 ("canu","Canu","assemble",["ont","hifi"],"marbl/canu","canu",None,"Overlap-layout-consensus assembler.","",[]),
 ("raven","Raven","assemble",["ont"],"lbcb-sci/raven","raven-assembler",None,"Fast OLC assembler.","",[]),
 ("megahit","MEGAHIT","assemble",["sr"],"voutcn/megahit","megahit",None,"Memory-efficient short-read metagenome assembler.","",[]),
 ("spades","SPAdes / metaSPAdes","assemble",["sr","ont","hifi"],"ablab/spades","spades",None,"de Bruijn assembler with metagenome and hybrid modes.","",[]),
 ("unicycler","Unicycler","assemble",["sr","ont"],"rrwick/Unicycler","unicycler",None,"Hybrid isolate assembler.","Long-read-first approaches now usually better.",[]),
 ("hybracter","hybracter","assemble",["ont","sr"],"gbouras13/hybracter","hybracter",None,"Automated long-read-first isolate assembly with plasmid recovery.","",[]),
 ("plassembler","plassembler","assemble",["ont","sr"],"gbouras13/plassembler","plassembler",None,"Plasmid recovery from isolate data.","",[]),
 ("dnaapler","dnaapler","assemble",["ont","hifi","sr"],"gbouras13/dnaapler","dnaapler",None,"Reorients circular chromosomes/plasmids to start genes.","",[]),
 # polish
 ("medaka","medaka","polish",["ont"],"nanoporetech/medaka","medaka",None,"ONT consensus polishing with basecaller-matched models.","Model must match basecaller version; can hurt metagenomes with strain mixtures.",[]),
 ("dorado_polish","Dorado polish","polish",["ont"],"nanoporetech/dorado",None,None,"Medaka-style polishing inside Dorado (GPU).","",[]),
 ("racon","Racon","polish",["ont","hifi"],"lbcb-sci/racon","racon",None,"Generic consensus polisher.","",[]),
 ("polypolish","Polypolish","polish",["sr"],"rrwick/Polypolish","polypolish",None,"Short-read polishing using all alignments (repeat-aware).","",[]),
 ("pypolca","pypolca","polish",["sr"],"gbouras13/pypolca","pypolca",None,"Python POLCA short-read polisher.","Pair with Polypolish.",[]),
 # bin
 ("semibin2","SemiBin2","bin",["ont","hifi","sr"],"BigDataBiology/SemiBin","semibin",None,"Self-supervised binning with long-read mode.","",[]),
 ("metacat","MetaCAT","bin",["ont","hifi","sr"],"liu-congcong/MetaCAT","metacat",None,"Metagenome binning by coverage and composition clustering.","Default binner in aviary 0.14.",[]),
 ("comebin","COMEBin","bin",["ont","hifi","sr"],"ziyewang/COMEBin","comebin",None,"Contrastive-learning binner.","",[]),
 ("vamb","VAMB / TaxVAMB","bin",["ont","hifi","sr"],"RasmussenLab/vamb","vamb",None,"Variational-autoencoder binner, optional taxonomy guidance.","",[]),
 ("metabat2","MetaBAT 2","bin",["ont","hifi","sr"],None,"metabat2","https://bitbucket.org/berkeleylab/metabat","Classic composition+coverage binner.","",[]),
 ("graphmb","GraphMB","bin",["ont"],"MicrobialDarkMatter/GraphMB","graphmb",None,"Uses the assembly graph to bin long-read assemblies.","",[]),
 ("binette","Binette","bin",["ont","hifi","sr"],"genotoul-bioinfo/Binette","binette",None,"Bin refinement across binners (DAS Tool successor approach).","",[]),
 ("dastool","DAS Tool","bin",["ont","hifi","sr"],"cmks/DAS_Tool","das_tool",None,"Consensus bin selection.","",[]),
 # magqc
 ("checkm2","CheckM2","magqc",["ont","hifi","sr"],"chklovski/CheckM2","checkm2",None,"ML completeness/contamination for MAGs.","",[]),
 ("checkm","CheckM","magqc",["ont","hifi","sr"],"Ecogenomics/CheckM","checkm-genome",None,"Marker-gene completeness/contamination.","Superseded by CheckM2 for most uses.",["legacy"]),
 ("gunc","GUNC","magqc",["ont","hifi","sr"],"grp-bork/gunc","gunc",None,"Detects chimeric genomes.","Catches chimerism CheckM misses.",[]),
 ("drep","dRep","magqc",["ont","hifi","sr"],"MrOlm/drep","drep",None,"Genome dereplication by ANI.","",[]),
 ("galah","galah","magqc",["ont","hifi","sr"],"wwood/galah","galah",None,"Fast dereplication with skani/FastANI.","",[]),
 ("quast","QUAST / metaQUAST","magqc",["ont","hifi","sr"],"ablab/quast","quast",None,"Assembly evaluation, with references if available.","",[]),
 ("busco","BUSCO","magqc",["ont","hifi","sr"],None,"busco","https://busco.ezlab.org","Single-copy ortholog completeness.","Eukaryotic bins.",[]),
 ("checkv","CheckV","magqc",["ont","hifi","sr"],None,"checkv","https://bitbucket.org/berkeleylab/checkv","Viral genome completeness and contamination.","",[]),
 # taxonomy
 ("gtdbtk","GTDB-Tk","taxonomy",["ont","hifi","sr"],"Ecogenomics/GTDBTk","gtdbtk",None,"GTDB classification of bacterial/archaeal genomes.","Version must match the GTDB release.",[]),
 ("cat_bat","CAT / BAT","taxonomy",["ont","hifi","sr"],"MGXlab/CAT_pack","cat",None,"Contig and bin taxonomy from protein hits.","Includes eukaryotes.",[]),
 # annotate
 ("bakta","Bakta","annotate",["ont","hifi","sr"],"oschwengers/bakta","bakta",None,"Standardised bacterial genome annotation.","Successor to Prokka.",[]),
 ("prokka","Prokka","annotate",["ont","hifi","sr"],"tseemann/prokka","prokka",None,"Rapid prokaryotic annotation.","Little development; prefer Bakta.",["legacy"]),
 ("pyrodigal","Pyrodigal","annotate",["ont","hifi","sr"],"althonos/pyrodigal","pyrodigal",None,"Fast Prodigal gene calling in Python.","",[]),
 ("eggnog","eggNOG-mapper","annotate",["ont","hifi","sr"],"eggnogdb/eggnog-mapper","eggnog-mapper",None,"Orthology-based functional annotation.","",[]),
 ("dram","DRAM","annotate",["ont","hifi","sr"],"WrightonLabCSU/DRAM","dram",None,"Metabolic annotation and summaries for MAGs.","",[]),
 ("antismash","antiSMASH","annotate",["ont","hifi","sr"],"antismash/antismash","antismash",None,"Biosynthetic gene cluster detection.","Long-read MAGs give far more complete BGCs.",[]),
 ("amrfinder","AMRFinderPlus","annotate",["ont","hifi","sr"],"ncbi/amr","ncbi-amrfinderplus",None,"NCBI AMR and virulence gene detection.","",[]),
 ("genomad","geNomad","annotate",["ont","hifi","sr"],"apcamargo/genomad","genomad",None,"Virus and plasmid identification.","",[]),
 ("diamond","DIAMOND","annotate",["ont","hifi","sr"],"bbuchfink/diamond","diamond",None,"Fast protein alignment.","",[]),
 ("mmseqs2","MMseqs2","annotate",["ont","hifi","sr"],"soedinglab/MMseqs2","mmseqs2",None,"Sensitive fast search and clustering.","",[]),
 ("kofamscan","KofamScan","annotate",["ont","hifi","sr"],None,"kofamscan","https://github.com/takaram/kofam_scan","KEGG Orthology assignment with HMMs.","",[]),
 # methyl
 ("modkit","modkit","methyl",["ont","hifi"],"nanoporetech/modkit",None,None,"Modified-base pileups, motif search and DMR from BAM MM/ML tags.","",[]),
 ("nanomotif","nanomotif","methyl",["ont"],"MicrobialDarkMatter/nanomotif","nanomotif",None,"De novo methylation motifs in MAGs, MTase linking, bin decontamination.","Methylation-aware bin cleaning and plasmid assignment.",[]),
 ("microbemod","MicrobeMod","methyl",["ont"],"cultivarium/MicrobeMod",None,None,"Bacterial methylation motifs and R-M system annotation.","",[]),
 ("methylartist","methylartist","methyl",["ont","hifi"],"adamewing/methylartist","methylartist",None,"Methylation plots from modified-base BAMs.","",[]),
 ("methbat","MethBat","methyl",["hifi"],"PacificBiosciences/MethBat",None,None,"PacBio methylation analysis toolkit.","Replaces pb-CpG-tools.",[]),
 ("pbcpg","pb-CpG-tools","methyl",["hifi"],"PacificBiosciences/pb-CpG-tools",None,None,"CpG pileups from HiFi.","Superseded by MethBat.",["legacy"]),
 # variants
 ("clair3","Clair3","variants",["ont","hifi","sr"],"HKU-BAL/Clair3","clair3",None,"Deep-learning small-variant caller.","",[]),
 ("sniffles2","Sniffles2","variants",["ont","hifi"],"fritzsedlazeck/Sniffles","sniffles",None,"Structural variant caller.","",[]),
 ("instrain","inStrain","variants",["sr","hifi"],"MrOlm/inStrain","instrain",None,"Microdiversity and strain comparison in metagenomes.","Built around short-read error profiles.",[]),
 ("strainy","Strainy","variants",["ont","hifi"],"katerinakazantseva/strainy","strainy",None,"Strain phasing of long-read metagenome assemblies.","",[]),
 ("floria","Floria","variants",["ont","hifi","sr"],"bluenote-1577/floria","floria",None,"Fast strain haplotype phasing in metagenomes.","",[]),
 # coverage
 ("coverm","CoverM","coverage",["ont","hifi","sr"],"wwood/CoverM","coverm",None,"Read coverage per contig/genome.","",[]),
 ("mosdepth","mosdepth","coverage",["ont","hifi","sr"],"brentp/mosdepth","mosdepth",None,"Fast depth calculation.","",[]),
 ("sourmash","sourmash","coverage",["ont","hifi","sr"],"sourmash-bio/sourmash","sourmash",None,"FracMinHash sketches, search and gather.","",[]),
 ("skani","skani","coverage",["ont","hifi","sr"],"bluenote-1577/skani","skani",None,"Fast accurate ANI, robust to incomplete MAGs.","",[]),
 ("mash","Mash","coverage",["ont","hifi","sr"],"marbl/Mash","mash",None,"MinHash distance estimation.","",[]),
 # workflow
 ("nfcore_mag","nf-core/mag","workflow",["sr","ont","hifi"],"nf-core/mag",None,None,"Assembly, binning and annotation pipeline.","Short-read first; long-read support growing.",[]),
 ("nfcore_taxprofiler","nf-core/taxprofiler","workflow",["sr","ont","hifi"],"nf-core/taxprofiler",None,None,"Multi-profiler taxonomic profiling.","",[]),
 ("wf_metagenomics","wf-metagenomics","workflow",["ont"],"epi2me-labs/wf-metagenomics",None,None,"EPI2ME read classification workflow (also 16S).","",[]),
 ("wf_bacterial","wf-bacterial-genomes","workflow",["ont"],"epi2me-labs/wf-bacterial-genomes",None,None,"EPI2ME isolate assembly and annotation.","",[]),
 ("mmlong2","mmlong2","workflow",["ont","hifi"],"Serka-M/mmlong2",None,None,"Long-read MAG recovery workflow (Microflora Danica scale).","",[]),
 ("aviary","Aviary","workflow",["ont","hifi","sr"],"rhysnewell/aviary","aviary",None,"Hybrid assembly, binning and annotation pipeline.","",[]),
 ("snakemake","Snakemake","workflow",["ont","hifi","sr"],"snakemake/snakemake","snakemake",None,"Python-based workflow engine.","",[]),
 ("nextflow","Nextflow","workflow",["ont","hifi","sr"],"nextflow-io/nextflow","nextflow",None,"Dataflow workflow engine behind nf-core and EPI2ME.","",[]),
 # viz
 ("bandageng","BandageNG","viz",["ont","hifi","sr"],"asl/BandageNG",None,None,"Assembly graph visualisation (maintained Bandage fork).","",[]),
 ("igv","IGV","viz",["ont","hifi","sr"],"igvteam/igv",None,None,"Genome browser incl. methylation colouring.","",[]),
 ("anvio","anvi'o","viz",["ont","hifi","sr"],"merenlab/anvio",None,None,"Interactive metagenomics and pangenomics platform.","",[]),
]

PLATFORMS = [
 {"id":"ont","name":"Oxford Nanopore","group":"long","chem":"R10.4.1 nanopore, 5 kHz","devices":"Flongle, MinION, GridION, PromethION (P2 Solo, P24, P48)","reads":"Tens of kb typical; ultra-long >100 kb possible","accuracy":"~Q20+ simplex with SUP models; higher for duplex","raw":"POD5 → BAM/FASTQ via Dorado","mods":"5mC, 5hmC, 6mA, 4mC natively from signal","role":"Our main platform: long-read MAGs, circular genomes, plasmids, methylation-aware binning. Watch for untrimmed adapters, barcodes and chimeras left after basecalling."},
 {"id":"hifi","name":"PacBio HiFi","group":"long","chem":"SMRT circular consensus","devices":"Revio, Vega","reads":"~15–20 kb HiFi reads","accuracy":">Q30 consensus","raw":"HiFi BAM","mods":"5mC; 6mA and 5hmC now reported on-instrument","role":"High-accuracy long-read metagenomes and full-length amplicons (Kinnex 16S). Residual adapters and concatemers need filtering."},
 {"id":"illumina","name":"Illumina","group":"sr","chem":"Sequencing by synthesis","devices":"NovaSeq X, NextSeq 2000, MiSeq i100","reads":"2×150 bp typical","accuracy":">Q30","raw":"BCL → FASTQ (BCL Convert/DRAGEN)","mods":"Via bisulfite/enzymatic conversion","role":"Deep, cheap coverage for profiling, strain variation and polishing."},
 {"id":"element","name":"Element AVITI","group":"sr","chem":"Avidity sequencing","devices":"AVITI, AVITI24","reads":"2×150 to 2×300 bp","accuracy":"Very high (Q40+ reported)","raw":"bases2fastq","mods":"Via conversion chemistries","role":"Short-read alternative with high base quality; same downstream tools."},
 {"id":"mgi","name":"MGI / Complete Genomics","group":"sr","chem":"DNA nanoball (DNBSEQ); CycloneSEQ nanopore","devices":"DNBSEQ-T7, G400; CycloneSEQ","reads":"2×150 bp (DNBSEQ)","accuracy":">Q30 (DNBSEQ)","raw":"FASTQ","mods":"—","role":"Low-cost short reads. CycloneSEQ availability in Europe is constrained by ONT patent litigation."},
 {"id":"ultima","name":"Ultima Genomics","group":"sr","chem":"Flow-based SBS on open wafer","devices":"UG 100","reads":"~300 bp single-end","accuracy":"High per-base, homopolymer indels are the main error","raw":"CRAM/FASTQ","mods":"—","role":"Very low cost per Gb for deep profiling; check homopolymer handling."},
 {"id":"sbx","name":"Roche SBX","group":"sr","chem":"Sequencing by expansion (Xpandomers read on a CMOS nanopore array)","devices":"Roche SBX system","reads":"Short-to-medium reads","accuracy":"Simplex and duplex modes","raw":"FASTQ/BAM","mods":"—","role":"New 2026 high-throughput entrant; tool compatibility still settling."},
]

def main(out):
    os.makedirs(out, exist_ok=True)
    ids = set()
    tools = []
    for (i,n,s,p,repo,bc,url,d,note,flags) in T:
        assert i not in ids, i; ids.add(i)
        assert s in [x[0] for x in STEPS], s
        tools.append({"id":i,"name":n,"step":s,"platforms":p,"repo":repo,"bioconda":bc,
                      "url":url or (f"https://github.com/{repo}" if repo else None),
                      "desc":d,"note":note,"flags":flags})
    json.dump({"steps":[{"id":a,"name":b,"desc":c} for a,b,c in STEPS],"tools":tools},
              open(f"{out}/catalogue.json","w"),indent=1,ensure_ascii=False)
    json.dump(PLATFORMS, open(f"{out}/platforms.json","w"),indent=1,ensure_ascii=False)
    print(len(tools),"tools")

if __name__=="__main__":
    import sys; main(sys.argv[1] if len(sys.argv)>1 else "data")
