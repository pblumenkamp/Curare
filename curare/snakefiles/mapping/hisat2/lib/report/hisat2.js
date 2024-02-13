'use strict';

new Vue({
    el: '#hisat2',
    data: {
        hisat2_stats: Curare.hisat2.stats,
        paired_end: Curare.hisat2.paired_end,
        hisat2_settings: Curare.hisat2.settings,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: [],
        bw2_settings_columns: [
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
        bw2_settings_data: function() {
            let vue = this
            let settings = [
                {
                    key: "HISAT2 Version",
                    value: vue.hisat2_settings["hisat2_version"] 
                },
                {
                    key: "Sequencing Strategy",
                    value: (vue.paired_end) ? "Paired-End" : "Single-End"
                },
                {
                    key: "Used Shared-Memory Mode (-mm)",
                    value: (vue.hisat2_settings["use_shared_memory"] === "true") ? "True" : "False"
                },
                {
                    key: "Additional HISAT2 Parameters",
                    value: (vue.hisat2_settings["additional_parameters"]) ? '"' + vue.hisat2_settings["additional_parameters"] + '"' : "-"
                }
            ]
            return settings
        }
    },
    methods: {}
});
