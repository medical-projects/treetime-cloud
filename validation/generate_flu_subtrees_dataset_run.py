#!/usr/bin/env python
import treetime
import numpy as np
import os,sys
import datetime
import subprocess
import re

import utility_functions_flu as flu_utils
import utility_functions_general as gen_utils
from utility_functions_beast import run_beast

aln_name = "./resources/flu_H3N2/H3N2_HA_2011_2013.fasta"
tree_name = "./resources/flu_H3N2/H3N2_HA_2011_2013.nwk"

RUN_TREETIME = True
RUN_LSD = True
RUN_BEAST = True


def sample_subtree(out_dir, N_leaves, subtree_fname_suffix):
    subtrees_dir = os.path.join(out_dir, "subtrees")
    if not os.path.exists(subtrees_dir):
        try:
            os.makedirs(subtrees_dir)
        except:
            pass
    subtree_fname_format = "H3N2_HA_2011_2013_{}_{}.nwk".format(N_leaves, subtree_fname_suffix)
    subtree_filename = os.path.join(subtrees_dir, subtree_fname_format)
    tree = flu_utils.subtree_with_same_root(tree_name, N_leaves, subtree_filename)
    N_leaves = tree.count_terminals()
    return subtree_filename, N_leaves

if __name__ == "__main__":

    N_leaves = int(sys.argv[1])
    out_dir = sys.argv[2]
    subtree_fname_suffix = sys.argv[3]
    treetime_res_file = sys.argv[4]
    lsd_res_file = sys.argv[5]

    if len(sys.argv) > 6:
        lsd_params = sys.argv[6].split("|")
    else:
        lsd_params = ['-c', '-r', 'a', '-v']



    #  Sample subtree
    subtree_filename, N_leaves = sample_subtree(out_dir, N_leaves, subtree_fname_suffix)

    if RUN_TREETIME:
        dates = flu_utils.dates_from_flu_tree(tree_name)
        myTree = treetime.TreeTime(gtr='Jukes-Cantor',
            tree=subtree_filename, aln=aln_name, dates=dates,
            debug=False, verbose=4)
        myTree.optimize_seq_and_branch_len(reuse_branch_len=True, prune_short=True, max_iter=5, infer_gtr=False)
        start = datetime.datetime.now()
        myTree.run(root='best', relaxed_clock=False, max_iter=3, resolve_polytomies=True, do_marginal=False)
        end = datetime.datetime.now()
        with open(treetime_res_file, 'a') as of:
            of.write("{},{},{},{},{},{},{}\n".format(
                subtree_filename,
                str(N_leaves),
                str(myTree.tree.root.numdate),
                str(myTree.date2dist.clock_rate),
                str(myTree.date2dist.r_val),
                str(gen_utils.internal_regress(myTree)),
                str((end-start).total_seconds())    ))
        print ("TreeTime done!")
    else:
        print ("Skip TreeTime run")


    if RUN_LSD:
        lsd_outdir = os.path.join(out_dir, 'LSD_out')
        #  run LSD for the subtree:
        if not os.path.exists(lsd_outdir):
            try:
                os.makedirs(lsd_outdir)
            except:
                pass
        lsd_outfile = os.path.join(lsd_outdir, os.path.split(subtree_filename)[-1].replace(".nwk", ".txt"))
        datesfile = os.path.join(lsd_outdir, os.path.split(subtree_filename)[-1].replace(".nwk", ".lsd_dates.txt"))
        flu_utils.create_LSD_dates_file_from_flu_tree(subtree_filename, datesfile)
        runtime = gen_utils.run_LSD(subtree_filename, datesfile, lsd_outfile, lsd_params)
        #  parse LSD results
        tmrca, mu, objective = gen_utils.parse_lsd_output(lsd_outfile)
        try:
            if float(mu) > 0:
                with open(lsd_res_file, "a") as of:
                    of.write(",".join([subtree_filename, str(N_leaves), tmrca, mu, runtime, objective]))
                    of.write("\n")
        except:
            pass

        print ("LSD Done!")
    else:
        print ("Skip LSD run")

    if RUN_BEAST:
        dates = flu_utils.dates_from_flu_tree(tree_name)
        beast_out_dir = os.path.join(out_dir, 'beast_out')
        if not os.path.exists(beast_out_dir):
            try:
                os.makedirs(beast_out_dir)
            except:
                pass
        beast_prefix = os.path.join(beast_out_dir, os.path.split(subtree_filename)[-1][:-4])  # truncate '.nwk'
        run_beast(subtree_filename, aln_name, dates, beast_prefix, template_file="./resources/beast/template_bedford_et_al_2015.xml")






