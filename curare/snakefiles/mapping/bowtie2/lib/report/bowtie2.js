'use strict';

new Vue({
    el: '#bowtie2',
    data: {
        bowtie2_stats: Curare.bowtie2.stats,
        paired_end: Curare.bowtie2.paired_end,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: []
    },
    computed: {},
    methods: {}
});
