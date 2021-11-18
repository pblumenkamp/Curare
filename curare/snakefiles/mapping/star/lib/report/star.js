'use strict';

new Vue({
    el: '#star',
    data: {
        star_stats: Curare.star.stats,
        star_settings: Curare.star.settings,
        paired_end: Curare.star.paired_end,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: [],
        star_settings_columns: [
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
        star_settings_data: function() {
            let vue = this
            let settings = [
                {
                    key: "STAR Version",
                    value: vue.star_settings["star_version"] 
                },
                {
                    key: "Sequencing Strategy",
                    value: (vue.paired_end) ? "Paired-End" : "Single-End"
                },
                {
                    key: "Reference Genome",
                    value: vue.star_settings["reference_genome"] 
                },
                {
                    key: "Genome Annotation",
                    value: vue.star_settings["genome_annotation"] 
                },
                {
                    key: "Annotation Parent Keyword (--sjdbGTFtagExonParentGene)",
                    value: vue.star_settings["annotation_parent_keyword"] 
                },
                {
                    key: "Annotation ID Keyword (--sjdbGTFtagExonParentTranscript)",
                    value: vue.star_settings["annotation_id_keyword"] 
                },
                {
                    key: "Annotation Feature Type (--sjdbGTFfeatureExon)",
                    value: vue.star_settings["annotation_feature_type"] 
                },
                {
                    key: "Additional STAR Index Parameters",
                    value: vue.star_settings["additional_star_index_parameters"]
                },
                {
                    key: "Additional STAR Mapping Parameters",
                    value: vue.star_settings["additional_star_index_parameters"]
                }
            ]
            return settings
        }
    },
    methods: {}
});
