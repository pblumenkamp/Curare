'use strict';

new Vue({
    el: '#edger',
    data: {
        counttable: Curare.edger.featurecounts,
        edger_comparisons: Curare.edger.edger_summary,
        feature_assignment: Curare.edger.feature_assignment,
        paired_end: Curare.edger.paired_end,
        fc_main_feature: Curare.edger.fc_main_feature,
        count_table_path: Curare.edger.count_table_path,
        edger_folder_path: Curare.edger.edger_dir_path,
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
        edger_summary_table: function () {
            const vue = this
            const tables = []
            for (const row of vue.edger_comparisons) {
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
        edger_keys: function () {
            var vue = this
            var comp_keys = vue.edger_comparisons.map((x, i) => [x.comparison, i])
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
            Chart.defaults.font.size = 16;
            vue.charts[chartId] = new Chart(ctx, {
                type: type,
                data: data,
                options: options,
            });
        },
        create_lfc_distribution_chart() {
            const vue = this
            const active_menu = vue.active_comparison_menu
            const comparison = vue.edger_comparisons[vue.edger_keys[active_menu][1]]
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
                        backgroundColor: 'rgba(72,120,208,1)',
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
      active_comparison_menu: function () {
          this.create_lfc_distribution_chart()
      }
    },
    mounted: function () {
        const vue = this
        this.$nextTick(function () {
            this.create_lfc_distribution_chart()
        })
    }
});
