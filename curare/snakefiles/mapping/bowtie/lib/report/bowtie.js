'use strict';

new Vue({
    el: '#bowtie',
    data: {
        bowtie_stats: Curare.bowtie.stats,
        paired_end: Curare.bowtie.paired_end,
        bowtie_settings: Curare.bowtie.settings,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: [],
        bw_settings_columns: [
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
        bw_settings_data: function() {
            let vue = this
            let settings = [
                {
                    key: "Bowtie Version",
                    value: vue.bowtie_settings["bowtie_version"] 
                },
                {
                    key: "Sequencing Strategy",
                    value: (vue.paired_end) ? "Paired-End" : "Single-End"
                },
                {
                    key: "Used Shared-Memory Mode (-mm)",
                    value: (vue.bowtie_settings["use_shared_memory"] === "true") ? "True" : "False"
                },
                {
                    key: "Additional Bowtie Parameters",
                    value: (vue.bowtie_settings["additional_parameters"]) ? '"' + vue.bowtie_settings["additional_parameters"] + '"' : "-"
                }
            ]

            if (vue.bowtie_settings["allowed_overall_mismatches"] != "/") {
                settings.splice(3, 0, {
                    key: "Allowed Overall Mismatches (-v)",
                    value: vue.bowtie_settings["allowed_overall_mismatches"]
                })
            }

            return settings
        }
    },
    methods: {}
});
