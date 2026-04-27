function return_response = freq_tuning_wrapper(stimuli_times,stimuli_stamps,spike_times,spike_clusters,clusters_list)

drcDir = 'D:\BarakH_codes\Sound_Pardigms\NP_Paradigm2\DRC Tuning';

maxDrcNum = size(dir([drcDir '/*.mat']),1);
DRC_TUNING_BASE_ID = 400;
DRC_TUNING_LAST_POSSIBLE_ID = 600;
nFirstChordsToIgnore = 0;  %5
iFreqToIgnore = 36; %Anomaly for highest frequency (too many responsive units) - removed in order to not bias the dataset for tuning analysis
% iFreqToIgnore = [];

drcs = cell(maxDrcNum,1);
drcStartTimesSecAll = cell(maxDrcNum,1);
for iDrc = 1:maxDrcNum
    drcs{iDrc} = load([drcDir filesep sprintf('DRC_%03g.mat',iDrc)]);
    drcStartTimesSecAll{iDrc} = stimuli_times(stimuli_stamps==(iDrc + DRC_TUNING_BASE_ID));
end

nClus = numel(clusters_list);

for iClus = 1:nClus
    tic;
    spikeTimesSec = spike_times(spike_clusters == clusters_list(iClus));
    response(iClus) = getDrcTuningAndContext(spikeTimesSec, ...
                    drcStartTimesSecAll, drcs,...
                    nFirstChordsToIgnore, [],iFreqToIgnore);
    fprintf('Clus %d     %3gs\n',clusters_list(iClus),toc);

end

for i = 1:numel(response)
    return_response(i).significantBonferroni = response(i).stats.significantBonferroni;
    return_response(i).timesPsthMs = response(i).timesPsthMs;
    return_response(i).freqs = response(i).freqs.valid;
    return_response(i).psthPerFreq = response(i).psthPerFreq;
end

end