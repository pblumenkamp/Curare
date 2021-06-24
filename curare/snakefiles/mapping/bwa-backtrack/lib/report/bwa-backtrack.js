'use strict';

new Vue({
    el: '#bwa',
    data: {
        bwa_stats: Curare.bwa_backtrack.stats,
        paired_end: Curare.bwa_backtrack.paired_end,
        bwa_settings: Curare.bwa_backtrack.settings,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: [],
        bwa_settings_columns: [
            {
                field: 'key',
                label: 'Key',
                visible: true
            },
            {
                field: 'value',
                label: 'Value',
                visible: true
            }
        ]
    },
    computed: {
        bwa_settings_data: function() {
            let vue = this
            let samse_sampe_key = (vue.paired_end) ? "additional_sampe_parameters" : "additional_samse_parameters"  
            let settings = [
                {
                    key: "BWA Version",
                    value: vue.bwa_settings["bwa_version"] 
                },
                {
                    key: "Sequencing Strategy",
                    value: (vue.paired_end) ? "Paired-End" : "Single-End"
                },
                {
                    key: "Additional BWA ALN Parameters",
                    value: (vue.bwa_settings["additional_aln_parameters"]) ? '"' + vue.bwa_settings["additional_aln_parameters"] + '"' : "-"
                },
                {
                    key: (vue.paired_end) ? "Additional BWA SAMPE Parameters" : "Additional BWA SAMSE Parameters",
                    value: (vue.bwa_settings[samse_sampe_key]) ? '"' + vue.bwa_settings[samse_sampe_key] + '"' : "-"
                },
            ]
            return settings
        }
    },
    methods: {}
});
