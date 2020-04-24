'use strict';

new Vue({
    el: '#trim-galore',
    data: {
        trim_galore_stats: Curare.trim_galore.stats,
        paired_end: Curare.trim_galore.paired_end,
        activeTab: 0,
        adapter_overview_columns: [
            {
                field: 'sequence',
                label: 'Sequence'
            },
            {
                field: 'type',
                label: 'Type'
            },
            {
                field: 'length',
                label: 'Length'
            },
            {
                field: 'trimmed',
                label: 'Trimmed Sequences'
            },
        ],
        allowed_errors_columns: [
            {
                field: 'range',
                label: 'Range'
            },
            {
                field: 'count',
                label: 'Allowed Errors'
            },
        ],
        preceeding_bases_columns: [
            {
                field: 'A',
                label: 'A'
            },
            {
                field: 'C',
                label: 'C'
            },
            {
                field: 'G',
                label: 'G'
            },
            {
                field: 'T',
                label: 'T'
            },
            {
                field: 'none/other',
                label: 'None/Other'
            },
        ],
        removed_sequences_columns: [
            {
                field: 'length',
                label: 'Length'
            },
            {
                field: 'count',
                label: 'Count'
            },
            {
                field: 'expect',
                label: 'Expect'
            },
            {
                field: 'max_err',
                label: 'Max. Error'
            },
            {
                field: 'error counts',
                label: 'Error Counts'
            },
        ],
    },
    computed: {
        samples: function() {
            const vue = this
            return Object.keys(vue.trim_galore_stats)
        },
        run_parameters: function() {
            const vue = this
            const all_run_parameters = []
            for (const sample of vue.samples) {
                const sample_parameters = vue.trim_galore_stats[sample]['Runtime Parameters']
                const table = [
                    {'key': 'Sample', 'value': sample},
                    {'key': 'Trimming Mode', 'value': sample_parameters['trimming_mode']},
                    {'key': 'Trim Galore Version', 'value': sample_parameters['trim_galore_version']},
                    {'key': 'Cutadapt Version', 'value': sample_parameters['cutadapt_version']},
                    {'key': 'Quality Phred Score Cutoff', 'value': sample_parameters['phred_score_cutoff']},
                    {'key': 'Quality Encoding Type', 'value': sample_parameters['encoding_type_selected']},
                    {'key': 'Adapter Sequence (Forward Reads)', 'value': sample_parameters['adapter_sequence_forward']},
                    {'key': 'Adapter Sequence (Reverse Reads)', 'value': sample_parameters['adapter_sequence_reverse']},
                    {'key': 'Maximum Trimming Error Rate', 'value': sample_parameters['max_trimming_error_rate']},
                    {'key': 'Minimum Required Adapter Overlap (Stringency)', 'value': sample_parameters['min_adapter_overlap']},
                    {'key': 'Minimum Required Sequence Length', 'value': sample_parameters['min_sequence_length']},
                    {'key': 'Length Cutoff (Forward Reads)', 'value': sample_parameters['length_cutoff_forward']},
                    {'key': 'Length Cutoff (Reverse Reads)', 'value': sample_parameters['length_cutoff_reverse']}
                ]
                all_run_parameters.push(table)
            }
            return all_run_parameters
        },
        summary: function() {
            const vue = this
            const getRatio = vue.getRatio
            const summaries = []
            for (const sample of vue.samples) {
                const summary = []
                for (const strand of ["Forward", "Reverse"]) {
                    const summary_data = vue.trim_galore_stats[sample][strand]
                    const table = [
                        {
                            'key': 'Total Reads Processed',
                            'value': summary_data['total_reads_processed']
                        },
                        {
                            'key': 'Reads With Adapters',
                            'value': `${summary_data['reads_with_adapters']} (${getRatio(summary_data['reads_with_adapters'], summary_data['total_reads_processed'])}%)`
                        },
                        {
                            'key': 'Reads Written (Passing Filters)',
                            'value': `${summary_data['reads_passing_filters']} (${getRatio(summary_data['reads_passing_filters'], summary_data['total_reads_processed'])}%)`
                        },
                        {'key': '', 'value': ''},
                        {
                            'key': 'Total Basepairs Processed',
                            'value': summary_data['total_basepairs_processed']
                        },
                        {
                            'key': 'Quality-Trimmed',
                            'value': `${summary_data['basepairs_quality_trimmed']} (${getRatio(summary_data['basepairs_quality_trimmed'], summary_data['total_basepairs_processed'])}%)`
                        },
                        {
                            'key': 'Total Written (Filtered)',
                            'value': `${summary_data['basepairs_passing_filters']} (${getRatio(summary_data['basepairs_passing_filters'], summary_data['total_basepairs_processed'])}%)`
                        },
                    ]
                    summary.push(table)
                }
                summaries.push(summary)
            }
            return summaries
        },
        adapter_overview: function() {
            const vue = this
            const getRatio = vue.getRatio
            const overviews = []
            for (const sample of vue.samples) {
                const overview = []
                for (const strand of ["Forward", "Reverse"]) {
                    const overview_data = vue.trim_galore_stats[sample][strand]
                    const table = [
                        {
                            'sequence': overview_data['adapter_overview']['sequence'],
                            'type': overview_data['adapter_overview']['type'],
                            'length': overview_data['adapter_overview']['length'],
                            'trimmed': `${overview_data['adapter_overview']['trimmed']} (${getRatio(overview_data['adapter_overview']['trimmed'], overview_data['total_reads_processed'])}%)`
                        },
                    ]
                    overview.push(table)
                }
                overviews.push(overview)
            }
            return overviews
        },
        adapter_allowed_errors: function() {
            const vue = this
            const all_allowed_errors = []
            for (const sample of vue.samples) {
                const sample_allowed_errors = []
                for (const strand of ["Forward", "Reverse"]) {
                    const allowed_errors_data = vue.trim_galore_stats[sample][strand]['allowed_errors']
                    const table = []
                    for (const row of allowed_errors_data) {
                        table.push({
                            'range': row['range'],
                            'count': row['count']
                        })
                    }
                    sample_allowed_errors.push(table)
                }
                all_allowed_errors.push(sample_allowed_errors)
            }
            return all_allowed_errors
        },
        adapter_preceeding_bases: function() {
            const vue = this
            const all_preceding_bases = []
            for (const sample of vue.samples) {
                const sample_preceding_bases = []
                for (const strand of ["Forward", "Reverse"]) {
                    const preceding_bases_data = vue.trim_galore_stats[sample][strand]['bases_preceding_adapter']
                    sample_preceding_bases.push([{
                        "A": preceding_bases_data["A"],
                        "C": preceding_bases_data["C"],
                        "G": preceding_bases_data["G"],
                        "T": preceding_bases_data["T"],
                        "none/other": preceding_bases_data["none/other"],
                    }])
                }
                all_preceding_bases.push(sample_preceding_bases)
            }
            return all_preceding_bases
        },
        adapter_removed_sequences: function() {
            const vue = this
            const all_removed_sequences = []
            for (const sample of vue.samples) {
                const sample_removed_sequences = []
                for (const strand of ["Forward", "Reverse"]) {
                    const removed_sequences_data = vue.trim_galore_stats[sample][strand]['removed_sequences']
                    const table = []
                    for (const row of removed_sequences_data) {
                        table.push({
                            "length": row["length"],
                            "count": row["count"],
                            "expect": row["expect"],
                            "max_err": row["max.err"],
                            "error counts": row["error counts"]
                        })
                    }
                    sample_removed_sequences.push(table)
                }
                all_removed_sequences.push(sample_removed_sequences)
            }
            return all_removed_sequences
        }
    },
    methods: {
        getRatio: (dividend, divisor, fractionDigits=1) => {
            dividend = parseFloat(dividend.replace(/,/g, ""))
            divisor = parseFloat(divisor.replace(/,/g, ""))
            return (dividend / divisor * 100).toFixed(fractionDigits)
        },
        createChart(chartId, type, data, options) {
            const ctx = document.getElementById(chartId);
            const myChart = new Chart(ctx, {
                type: type,
                data: data,
                options: options,
            });
        },
        create_preceeding_bases_chart() {
            const vue = this
            for (const [i, strand] of ['Forward', 'Reverse'].entries()) {
                const preceeding_bases = vue.trim_galore_stats[vue.samples[vue.activeTab]][strand]['bases_preceding_adapter']
                const datapoints = [
                    parseFloat(preceeding_bases['A']),
                    parseFloat(preceeding_bases['C']),
                    parseFloat(preceeding_bases['G']),
                    parseFloat(preceeding_bases['T']),
                    parseFloat(preceeding_bases['none/other']),
                ]
                this.createChart(
                    `preceeding_bases_${vue.activeTab}_${i}`,
                    'pie',
                    {
                        datasets: [{
                            data: datapoints,
                            backgroundColor: [
                                'rgba(0,114,178,1)',
                                'rgba(204,121,167,1)',
                                'rgba(0,158,115,1)',
                                'rgba(213,94,0,1)',
                                'rgba(0,0,0,1)'
                            ]
                        }],
                        labels: [
                            "A", "C", "G", "T", "None/Other"
                        ],
                    },
                    {
                        legend: {
                            position: 'bottom'
                        }
                    }
                )
            }
        },
        create_removed_sequences_chart() {
            const vue = this
            for (const [i, strand] of ['Forward', 'Reverse'].entries()) {
                const removed_sequences = vue.trim_galore_stats[vue.samples[vue.activeTab]][strand]['removed_sequences']
                const datapoints = []
                const labels = []
                const backgroundColor = []
                console.log(removed_sequences[removed_sequences.length-1]['length'])
                for (let i=1; i <= removed_sequences[removed_sequences.length-1]['length']; i++) {
                    console.log(i)
                    labels.push(i.toString())
                    datapoints.push(0)
                    backgroundColor.push('rgba(0,114,178,1)')
                }
                console.log(labels)
                console.log(datapoints)
                for (const row of removed_sequences) {
                    datapoints[parseInt(row['length'])-1] = parseInt(row['count'])
                }
                console.log(labels)
                console.log(datapoints)
                this.createChart(
                    `removed_sequences_${vue.activeTab}_${i}`,
                    'bar',
                    {
                        datasets: [{
                            data: datapoints,
                            backgroundColor: backgroundColor
                        }],
                        labels: labels,
                    },
                    {
                        legend: {
                            display: false
                        },
                        scales: {
                            xAxes: [{
                             scaleLabel: {
                                 display: true,
                                 labelString: 'Length'
                             }
                            }],
                            yAxes: [{
                                scaleLabel: {
                                    display: true,
                                    labelString: 'Count'
                                }
                            }]
                        }
                    }
                )
            }
        }
    },
    watch: {
        activeTab: function () {
            this.create_preceeding_bases_chart()
            this.create_removed_sequences_chart()
        }
    },
    mounted: function () {
        this.$nextTick(function () {
            this.create_preceeding_bases_chart()
            this.create_removed_sequences_chart()
        })
    }
});
