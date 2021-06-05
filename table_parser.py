import pathlib
from string import Template

import pandas as pd
from slugify import slugify

# Translate ST_FIPS to State
ST_FIPS = pd.read_csv('ST_FIPS.csv')

column_values = [
        'INSTNM',
        'INSTURL',
        'ST_FIPS',
        'PBI',
        'HBCU',
        'CURROPER',
        ]
df = pd.read_csv('Most-Recent-Cohorts-All-Data-Elements.csv', usecols=column_values) # TODO: `use_cols` to reduce the size of imported data

hbcus = df.loc[((df.PBI == 1) | (df.HBCU==1)) & (df.CURROPER==1)]
hbcus['slug'] = df.apply(lambda x: slugify(x['INSTNM']), axis=1)
hbcus = hbcus.merge(ST_FIPS, on='ST_FIPS')


def _gen_slug_link(school):
    """create markdown link to associated pages object"""

    return f"[{school.INSTNM}](/pages/{school.slug}.md) - {school.INSTURL}"


def gen_readme():
    """build readme with readme_templates"""
    hbcus['readme'] = hbcus.apply(_gen_slug_link, axis=1)

    states_list = []

    for name in sorted(hbcus["STATE"].unique()):
        schools = hbcus[hbcus["STATE"] == name]['readme'].values
        schools = "\n\n".join(schools)
        state_section = f"## {name}\n{schools}"
        states_list.append(state_section)

    state_sections = "\n\n".join(states_list)

    with open("README.md", "w") as fp:
        fp.write(f"""# HBCUs in the the United States
{state_sections}

#### source: 
- [College Scorecard US Dept. of Education](https://data.ed.gov/dataset/college-scorecard-all-data-files-through-6-2020/resources?resource=823ac095-bdfc-41b0-b508-4e8fc3110082)

#### license: [MIT License](/LICENSE)""")


def build_pages(): # TODO REMOVE DEPENDENCY ON WIKIPEDIA
    hbcus.set_index("School")
    hbcu_json = hbcus.to_dict(orient="records")

    for row in hbcu_json:
        f_meta = []

        for name, val in row.items():
            if name != "Comment":
                f_meta.append(f"{name}: {val}")

        ftext = "\n".join(f_meta)

        filepath = pathlib.Path(slugify(row["School"])).with_suffix(".md")
        page = pathlib.Path("pages").joinpath(filepath)

        page.write_text(
            f"""---
{ftext}
---
{row['Comment']}"""
        )


if __name__ == "__main__":
    gen_readme()
