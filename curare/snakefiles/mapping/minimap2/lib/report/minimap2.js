'use strict';

new Vue({
    el: '#minimap2',
    data: {
        minimap2_stats: Curare.minimap2.stats,
        paired_end: Curare.minimap2.paired_end,
        minimap2_settings: Curare.minimap2.settings,
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
                    key: "Minimap2 Version",
                    value: vue.minimap2_settings["minimap2_version"] 
                },
                {
                    key: "Sequencing Strategy",
                    value: (vue.paired_end) ? "Paired-End" : "Single-End"
                },
                {
                    key: "Used Minimap2 Preset",
                    value: (vue.minimap2_settings["preset"]) ? '"' + vue.minimap2_settings["preset"] + '"' : "-"
                },
                {
                    key: "Additional Minimap2 Index Parameters",
                    value: (vue.minimap2_settings["additional_index_parameters"]) ? '"' + vue.minimap2_settings["additional_index_parameters"] + '"' : "-"
                },
                {
                    key: "Additional Minimap2 Alignment Parameters",
                    value: (vue.minimap2_settings["additional_alignment_parameters"]) ? '"' + vue.minimap2_settings["additional_alignment_parameters"] + '"' : "-"
                }
            ]
            return settings
        }
    },
    methods: {}
});
