HELPFUL TIPS:

using "nohup <program_command> &" runs programs in the background



MASTER_PIPELINE WORKFLOW:
Start in the master_pipeline directory
cd <path_to_master_pipeline>/master_pipeline

1. GENERATE CANDIDATE PATHS

In order to generate candidate paths you need to navigate to the candidate_paths_java folder and edit the config file located in the hiv folder
to generate the paths you want. 

Node and Edge data are located in the candidate_paths_java/hiv/features and candidate_paths_java/hiv/networks directories

inside hiv_baseline.config is the configurations for path generation
EFEATURE represents the type of edges we have (i.e. rxn,ppi,ptmod,in_cx)
EDGE_LIBRARY says wher ethe edge files are located relative to the candidate_paths_java directory
NFEATURE is the type of nodes we have
The important lines in this file are the GAMS_FILE line which tells you where to output the gams files and the output prefix as well as the OUT_PREFIX line which represents the background network files and the output prefix for them.

For this baseline example our source nodes are located at:
./hiv/features/hiv_bkzyl.tab

and our targets are:
./hiv/features/agg_interfaces.tab

***If ./hiv/features does not contain a hits_plus_ints.tab file create it****
cat ./hiv/features/hiv_bkzyl.tab ./hiv/features/agg_interfaces.tab > ./hiv/features/hits_plus_ints.tab

INSTRUCTIONS:
Make sure java v7 is installed. to check run:
java -version
one of the lines should read "java version 1.7.X_XXX"

#go to candidate_paths directory
cd candidate_paths_java

#edit config file (optional)
vim hiv/hiv_baseline.config

#run candidate path algorithm
java -jar HIVMain.jar  hiv/hiv_baseline.config


OUTPUT:
This will output the following files in the following directory (assuming config file has not been changed, prefix = hiv_len3)
#master gams file
./hiv/gams/hiv_len3_master.gms

#master edge file
./hiv/cytoscape/hiv_len3_gamsID.edge

#edge features file
./hiv/cytoscape/hiv_len3_edge_feats.tab

#node feature file
./hiv/cytoscape/hiv_len3_node_feats.tab

#master paths files
./hiv/cytoscape/hiv_len3_paths.sif
./hiv/gams/hiv_len3_master_paths.tab

#master subgraphs files
./hiv/gams/hiv_len3_master_subgraphs.tab

#master background network file
./hiv/cytoscape/hiv_len3_background.sif

#master background without hiv nodes
./hiv/cytoscape/hiv_len3_background_no_hiv.sif

PERFORM SOME POST PROCESSING:
#fixes up certain issues with background network
python fix_bg_network.py ./hiv/cytoscape/hiv_len3_background_no_hiv.sif ./hiv/cytoscape/hiv_len3_background_no_hiv.sif


MOVE CERTAIN FILES TO OTHER DIRECTORIES (assuming current directory is master_pipeline/candidate_paths_java):
cp ./hiv/cytoscape/hiv_len3_background_no_hiv.sif ../kernel_python/input_networks
cp ./hiv/features/hits_plus_ints.tab ../kernel_python/input_hits

cp ./hiv/gams/hiv_len3_master_paths.tab ../condor_optimize/data/
cp ./hiv/gams/hiv_len3_master_subgraphs.tab ../condor_optimize/data/
cp ./hiv/gams/hiv_len3_master.gms ../condor_optimize/data/



2. RUN DIFFUSION KERNEL

We now have to run a diffusion kernel on our background network in order to generate samples and to weight our nodes

INSTRUCTIONS:
#Run diffusion kernel pipeline
bash run_kernel_everything output_dir input_networks/hiv_len3_backgorund_no_hiv_cx.sif input_hits/hits_plus_ints.tab

OUTPUT:
This will generate the follwoing files

#master labels file
./input_networks/hiv_len3_background_no_hiv_cx_master_labels.tab

#kernel file
./input_networks/hiv_len3_background_no_hiv_cx_kernel.npy

#output directory with multiple results for different sample sizes. We will be using 0.75
./output_dir

COPY CERTAIN FILES TO OTHER DIRECTORIES
cp ./input_networks/hiv_len3_background_no_hiv_cx_master_labels.tab ../condor_optimize/data/hiv_human_master_labels.tab
cp ./input_networks/hiv_len3_background_no_hiv_cx_master_labels.tab ../optimize_results/hiv_human_master_labels.tab

#copy hidden by file
cp ./output_dir/hiv_0.75_hidden_by_sample.tab ../condor_optimize/data
cp ./output_dir/hiv_0.75_hidden_by_sample.tab ../optimize_results/

#copy samples 
cp -r ./output_dir/sample0.75 ../condor_optimize/

#copy hit and interface list
cp ./output_dir/hiv_len3_background_no_hiv_cx_kernel_results/hiv_0.75_kernel_hit_and_interface.list ../optimize_results/

cp ./output_dir/hiv_by_degree.list ../condor_optimize/data/
cp ./output_dir/full_hits_scores.gms ../condor_optimize/data/


3. RUN OPTIMIZATION ON CHTC
We will run gams and the optimization on CHTC so copy the condor_optimize directory now filed with your intermediate files to the CHTC submit server

INSTRUCTIONS:
Move to master_pipeline directory

scp -rp condor_optimize <username>@submit-3.chtc.wisc.edu:~

Now log into chtc 

ssh <username>@submit-3.chtc.wisc.edu
Once logged in:

cd condor_optimize

look at the run_optimization.sh and make sure all the files listed are the same as the files you placed in the data directory
otherwise change the filenames to match
vim run_optimization.sh

Look at the submit file and make sure all files are copied correctly
vim condor_optimize.sub

run condor:
condor_submit condor_optimize.sub


Once completed you should have 100 .gdx files in your condor_optimize directory on chtc.

mkdir dump_results

mv *_dump ./dump_results/

Move the dump_results folder back to your directory on the BIOSTAT server where you performed steps 1 and 2. 

scp -rf dump_results <username>@biostat.wisc.edu:<path_to_master_pipeline>/optimize_results/

logout of CHTC and back into BIOSTAT

Log back into work server and go to your  master_pipeline directory make sure optimize_results/dump_results is present


4. INTERPRETING RESULTS

INSTURCTIONS:

python scripts/gather_path_solution_info.py "dump_folder/*_dump" dump_folder/pref
python ./scripts/eval_sample_results.py ./dump_folder ./hiv_0.75_hidden_by_sample.tab ./hiv_human_master_labels.tab hits_and_ints > ./pr_results/prefix_results.list


POST-PROCESSING
bash ./scripts/sort_ip_by_kernel.sh pr_results hiv_0.75_kernel_hit_and_interface.list 

E-Mail Sid once you are done with this step. 





