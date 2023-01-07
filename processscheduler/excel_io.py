# Copyright (c) 2020-2021 Thomas Paviot (tpaviot@gmail.com)
#
# This file is part of ProcessScheduler.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from binascii import crc32

try:
    import xlsxwriter

    HAVE_XLSXWRITER = True
except ImportError:
    HAVE_XLSXWRITER = False


def _get_color_from_string(a_string: str, colors: bool):
    if colors:
        hash_str = f"{crc32(a_string.encode('utf-8'))}"
        return f"#{hash_str[2:8]}"
    else:
        return "#F0F0F0"


def export_solution_to_excel_file(solution, excel_filename, colors: bool):
    """Export to excel.
    colors: a boolean flag. If True background colors are generated from
    the string hash, light gray otherwise.
    """
    if not HAVE_XLSXWRITER:
        raise ModuleNotFoundError("XlsxWriter is required but not installed.")

    workbook = xlsxwriter.Workbook(excel_filename)
    #
    # Resource worksheet
    #
    worksheet_resource = workbook.add_worksheet("GANTT Resource view")

    # widen the first column to make the text clearer.
    worksheet_resource.set_column("A:A", 20)
    # shorten following columns
    worksheet_resource.set_column("B:EC", 4)
    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({"bold": True})
    worksheet_resource.write("A1", "Resources", bold)  # {'bold': True})

    cell_resource_name_format = workbook.add_format({"align": "left"})
    cell_resource_name_format.set_font_size(12)

    # then loop over resources
    for i, resource_name in enumerate(solution.resources):
        # write the resource name on the first column
        worksheet_resource.write(i + 1, 0, resource_name, cell_resource_name_format)

        # get the related resource object
        ress = solution.resources[resource_name]

        for task_name, task_start, task_end in ress.assignments:
            # unavailabilities are rendered with a grey dashed bar
            text_to_display = "" if "NotAvailable" in task_name else task_name
            bg_color = _get_color_from_string(task_name, colors)

            cell_task_format = workbook.add_format({"align": "center"})
            cell_task_format.set_font_size(12)
            cell_task_format.set_border()
            cell_task_format.set_bg_color(bg_color)

            # if task duration is greater than 1, need to merge cells
            if task_end - task_start > 1:
                worksheet_resource.merge_range(
                    i + 1,  # row
                    task_start + 1,  # start column
                    i + 1,  # row
                    task_end,  # end column
                    text_to_display,
                    cell_task_format,
                )
            else:
                worksheet_resource.write(
                    i + 1, task_start + 1, task_name, cell_task_format
                )

    # finally close the workbook
    worksheet_resource.autofit()
    worksheet_resource.freeze_panes(1, 1)

    #
    # Task worksheet
    #
    worksheet_task = workbook.add_worksheet("GANTT Task view")

    # widen the first column to make the text clearer.
    worksheet_task.set_column("A:A", 20)
    # shorten following columns
    worksheet_task.set_column("B:EC", 4)
    # Add a bold format to use to highlight cells.
    worksheet_task.write("A1", "Tasks", bold)  # {'bold': True})

    # then loop over tasks
    for i, task_name in enumerate(solution.tasks):
        # write the resource name on the first column
        cell_task_name_format = workbook.add_format({"align": "left"})
        cell_task_name_format.set_font_size(12)
        worksheet_task.write(i + 1, 0, task_name, cell_task_name_format)

        # get the related resource object
        current_task = solution.tasks[task_name]

        text_to_display = ",".join(current_task.assigned_resources)

        # the color is computed from the resource names
        bg_color = _get_color_from_string(text_to_display, colors)

        cell_task_format = workbook.add_format({"align": "center"})
        cell_task_format.set_font_size(12)
        cell_task_format.set_border()
        cell_task_format.set_bg_color(bg_color)

        # if task duration is greater than 1, need to merge contiguous cells
        if current_task.end - current_task.start > 1:
            worksheet_task.merge_range(
                i + 1,  # row
                current_task.start + 1,  # start column
                i + 1,  # row
                current_task.end,  # end column
                text_to_display,
                cell_task_format,
            )
        else:
            worksheet_task.write(
                i + 1, current_task.start + 1, text_to_display, cell_task_format
            )

    worksheet_task.autofit()
    worksheet_task.freeze_panes(1, 1)

    #
    # Indicators
    #
    worksheet_indicator = workbook.add_worksheet("Indicators")
    worksheet_indicator.write("A1", "Indicator", bold)
    worksheet_indicator.write("B1", "Value", bold)

    cell_indicator_name_format = workbook.add_format({"align": "left"})
    cell_indicator_name_format.set_font_size(12)

    for i, indicator_name in enumerate(solution.indicators):
        worksheet_indicator.write(i + 1, 0, indicator_name, cell_indicator_name_format)

        indicator_value = solution.indicators[indicator_name]
        worksheet_indicator.write(i + 1, 1, indicator_value, cell_indicator_name_format)

    worksheet_indicator.autofit()

    # finally save the workbook
    workbook.close()
