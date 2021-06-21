'use strict';

new Vue({
    el: '#deseq2',
    data: {
        counttable: Curare.deseq2.featurecounts,
        deseq2_comparisons: Curare.deseq2.deseq2_summary,
        feature_assignment: Curare.deseq2.feature_assignment,
        paired_end: Curare.deseq2.paired_end,
        fc_main_feature: Curare.deseq2.fc_main_feature,
        counttable_in_percent: false,
        charts: {},
        counttable_columns: [
            {
                field: 'name',
                label: 'Sample',
                visible: true
            },
            {
                field: 'reads',
                label: 'Total Reads',
                visible: true,
                numeric: true
            },
            {
                field: 'Assigned',
                label: 'Assigned',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Unmapped',
                label: 'Unassigned Unmapped',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Read_Type',
                label: 'Unassigned Read Type',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Singleton',
                label: 'Unassigned Singleton',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_MappingQuality',
                label: 'Unassigned MappingQuality',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Chimera',
                label: 'Unassigned Chimera',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_FragmentLength',
                label: 'Unassigned FragmentLength',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Duplicate',
                label: 'Unassigned Duplicate',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_MultiMapping',
                label: 'Unassigned MultiMapping',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Secondary',
                label: 'Unassigned Secondary',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_NonSplit',
                label: 'Unassigned NonSplit',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_NoFeatures',
                label: 'Unassigned NoFeatures',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Overlapping_Length',
                label: 'Unassigned Overlapping_Length',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Ambiguity',
                label: 'Unassigned Ambiguity',
                visible: true,
                numeric: true
            }
        ],
        key_value_columns: [
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
        ],
        active_comparison_menu: "",
        active_feature_assignment_menu: "",
        currentPage: 1
    },
    computed: {
        reads_per_sample: function () {
            const vue = this
            const sums = []
            for (const row of vue.counttable) {
                let sum = 0
                for (const [key, value] of Object.entries(row)) {
                    if (key !== 'name') {
                        sum += parseFloat(value)
                    }
                }
                sums.push(sum)
            }
            return sums
        },
        counttable_table: function () {
            const vue = this
            if (vue.counttable_in_percent) {
                return vue.counttable_table_relative
            } else {
                return vue.counttable_table_absolute
            }
        },
        counttable_table_absolute: function () {
            const vue = this
            const data = vue.counttable
            for (const [i, row] of data.entries()) {
                row['reads'] = vue.reads_per_sample[i]
            }
            for (const col of vue.counttable_columns) {
                let all_zero = true
                for (const row of data) {
                    if (row[col['field']] !== '0') {
                        all_zero = false
                        break
                    }
                }
                if (all_zero) {
                    col['visible'] = false
                }
            }
            return data
        },
        counttable_table_relative: function () {
            const vue = this
            const data = vue.counttable_table_absolute
            const table = []
            for (const row of data) {
                const new_row = {}
                for (const [key, value] of Object.entries(row)) {
                    if (['name', 'reads'].includes(key)) {
                        new_row[key] = value
                    } else {
                        new_row[key] = ((parseFloat(value) / parseFloat(row['reads'])) * 100).toFixed(2)
                    }
                }
                table.push(new_row)
            }
            return table
        },
        deseq2_summary_table: function () {
            const vue = this
            const tables = []
            for (const row of vue.deseq2_comparisons) {
                tables.push([
                    {
                        'key': '',
                        'value': ''
                    },
                    {
                        'key': 'Lowest Log2 Fold Change',
                        'value': parseFloat(row['lowest_lfc']).toFixed(1)
                    },
                    {
                        'key': 'Lowest Log2 Fold Change (Name)',
                        'value': row['lowest_lfc_name']
                    },
                    {
                        'key': 'Highest Log2 Fold Change',
                        'value': parseFloat(row['highest_lfc']).toFixed(1)
                    },
                    {
                        'key': 'Highest Log2 Fold Change (Name)',
                        'value': row['highest_lfc_name']
                    },
                    {
                        'key': '',
                        'value': ''
                    },
                    {
                        'key': 'Adjusted P-value > 0.05',
                        'value': row['adjP_smaller_5']
                    },
                    {
                        'key': 'Adjusted P-value > 0.01',
                        'value': row['adjP_smaller_1']
                    },
                    {
                        'key': 'Adjusted P-value > 0.001',
                        'value': row['adjP_smaller_0.1']
                    },
                    {
                        'key': '',
                        'value': ''
                    },
                ])
            }
            return tables
        },
        feature_assignment_keys: function () {
            var vue = this
            var feature_keys = Object.keys(vue.feature_assignment)
            feature_keys.sort()
            vue.active_feature_assignment_menu = feature_keys[0]
            return feature_keys
        },
        deseq2_keys: function () {
            var vue = this
            var comp_keys = vue.deseq2_comparisons.map((x, i) => [x.comparison, i])
            comp_keys.sort((a, b) => {
                if (a[0] > b[0] ) {
                    return 1
                } else if (a[0] < b[0]) {
                    return -1
                }
                return 0
            })
            vue.active_comparison_menu = comp_keys[0][1]
            return comp_keys
        }
    },
    methods: {
        createChart(chartId, type, data, options) {
            const vue = this
            const ctx = document.getElementById(chartId);
            if (chartId in vue.charts && vue.charts[chartId] !== undefined) {
                vue.charts[chartId].destroy()
            }
            vue.charts[chartId] = new Chart(ctx, {
                type: type,
                data: data,
                options: options,
            });
        },
        create_stacked_bar_chart() {
            const vue = this
            const colors = [
                'rgba(0,160,250,1)',
                'rgba(10,155,75,1)',
                'rgba(255,130,95,1)',
                'rgba(250,120,250,1)',
                'rgba(160,250,130,1)',
                'rgba(170,10,60,1)',
                'rgba(0,110,130,1)',
                'rgba(234,214,68,1)',
                'rgba(130,20,160,1)',
                'rgba(20,210,220,1)',
                'rgba(0,90,200,1)',
                'rgba(250,230,130,1)',
                'rgba(0,0,0,1)',
                'rgba(125,125,125,1)'
            ]
            const datasets = []

            for (const [i, category] of vue.counttable_columns.entries()) {
                if (!['name', 'reads'].includes(category.field) && category.visible) {
                    const data = []
                    for (const row of vue.counttable_table) {
                        data.push(row[category.field])
                    }
                    const color = colors[i-2]  // 'name' and 'reads' don't need any color
                    datasets.push({
                        label: category.label,
                        data: data,
                        backgroundColor: data.map((x) => color),
                        borderColor: data.map((x) => color),
                        borderWidth: 2
                    })
                }
            }
            const chartID = 'stacked_barchart'
            var data = {
                datasets: datasets,
                labels: vue.counttable_table.map((x) => x['name']),
            }
            var options = {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    x: {
                      stacked: true,
                    },
                    y: {
                      stacked: true,
                      beginAtZero: true
                    }
                  }
            }

            if (vue.counttable_in_percent) {
                options.scales.y.max = 100
            }

            this.createChart(
                chartID,
                'bar',
                data,
                options
            )
        },
        create_lfc_distribution_chart() {
            const vue = this
            const active_menu = vue.active_comparison_menu
            const comparison = vue.deseq2_comparisons[vue.deseq2_keys[active_menu][1]]
            const data_label = comparison['lfc_distribution']['label']
            const data = comparison['lfc_distribution']['data']

            if (typeof comparison === 'undefined' || typeof data_label === 'undefined' || typeof data === 'undefined') {
                return
            }

            this.createChart(
                'lfc_distribution',
                'bar',
                {
                    labels: data_label,
                    datasets: [{
                        data: data,
                        backgroundColor: 'rgba(0,160,250,1)',
                        barPercentage: 0.95,
                        categoryPercentage: 1,
                        xAxisID: "xA"
                    }],
                },
                {
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        xA: {
                            display: false,
                            position: 'bottom',
                            max: data_label.length - 2,
                        },
                        x: {
                            display: true,
                            offset: false,
                            grid: {
      	                        offset: false
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: '#Features',
                            },
                            beginAtZero: true
                        }
                    }
                }
            )

        }
    },
    watch: {
      counttable_in_percent: function () {
          this.create_stacked_bar_chart()
      },
      active_comparison_menu: function () {
          this.create_lfc_distribution_chart()
      }
    },
    mounted: function () {
        const vue = this
        this.$nextTick(function () {
            this.create_stacked_bar_chart()
            this.create_lfc_distribution_chart()
        })
    }
});
