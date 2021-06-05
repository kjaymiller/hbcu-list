import pathlib

import pandas as pd
from slugify import slugify

from typer import Typer

app = Typer()

column_values = [
    "INSTNM",
    "INSTURL",
    "CITY",
    "ST_FIPS",
    "PBI",
    "HBCU",
    "CURROPER",
    "LATITUDE",
    "LONGITUDE",
    "MENONLY",
    "WOMENONLY",
    "CONTROL",
    "RELAFFIL",
]

base_df = pd.read_csv("Most-Recent-Cohorts-All-Data-Elements.csv", usecols=column_values)

# Create DATAFRAME FOR ACTIVE HBCUs and PBIs
hbcus = base_df.loc[(base_df.HBCU == 1) & (base_df.CURROPER == 1)]
pbis = base_df.loc[(base_df.PBI == 1) & (base_df.CURROPER == 1)]

def from_dict(df, csv_file, index_col, value, fill_value=0):
    dict_from_pandas = pd.read_csv(csv_file, index_col=index_col).to_dict(orient="index")
    df[index_col].fillna(fill_value, inplace=True)
    df[index_col] = df.apply(lambda x: dict_from_pandas[x[index_col]][value], axis=1) 


for df in (hbcus, pbis):
    df['slug'] = df.apply(lambda x: slugify(x.INSTNM), axis=1)

    # CREATE LOCATION COLUMN
    df["location"] = df.apply(lambda x: [x.LATITUDE, x.LONGITUDE], axis=1)


    # Replace Data from 
    # STATE DATA
    from_dict(
            df=df,
            csv_file="ST_FIPS.CSV",
            index_col='ST_FIPS',
            value='STATE',
    )

    # CONTROL DATA
    from_dict(
            df=df,
            csv_file="CONTROL.CSV",
            index_col='CONTROL',
            value='CONTROL_VALUE',
            fill_value=0,
    )

    # RELIGIOUS DATA -  Patch Found Invalid VALUE
    df.loc[df['RELAFFIL'] > 107, 'RELAFFIL'] = 99
    from_dict(
            df=df,
            csv_file="RELAFFIL.CSV",
            index_col='RELAFFIL',
            value='RELIGIOUS',
            fill_value=-1,
    )

def _gen_slug_link(school):
    """create markdown link to associated pages object"""
    return f"[{school.INSTNM}](/pages/{school.slug}.md) - {school.INSTURL}"


@app.command()
def gen_list(
        filename: pathlib.Path='readme.md',
        title="HBCUs in the the United States"
        ):
    """build readme with readme_templates"""

    hbcus["readme"]= hbcus.apply(_gen_slug_link, axis=1)
    pbi["readme"]= hbcus.apply(_gen_slug_link, axis=1)

    state_sections = {}

    for df_name, df in (('hbcus', hbcus), ('pbi', pbi)):
        states_list = []
        for name in sorted(df["ST_FIPS"].unique()):
            schools = df[df["ST_FIPS"] == name]["readme"].values
            schools = "\n\n".join(schools)
            state_section = f"## {name}\n{schools}"
            states_list.append(state_section)

        state_sections[df_name] = "\n\n".join(states_list)

        filename.write_text(
                f"""# {title}
## HBCUs by State
{state_sections[hbcus]}

## PBI by State
{state_sections[pbi]}

---
#### source: 
    - [College Scorecard US Dept. of Education](https://data.ed.gov/dataset/college-scorecard-all-data-files-through-6-2020/resources?resource=823ac095-bdfc-41b0-b508-4e8fc3110082)

#### license: [MIT License](/LICENSE)"""
            )

@app.command()
def build_pages(): # TODO REMOVE DEPENDENCY ON WIKIPEDIA
    hbcu_json = hbcus.to_dict(orient="records")

    for row in hbcu_json:
        f_meta = []

        for name, val in row.items():
            f_meta.append(f"{name}: {val}")

        ftext = "\n".join(f_meta)

        filepath = pathlib.Path(row["slug"]).with_suffix(".md")
        page = pathlib.Path("pages").joinpath(filepath)

        page.write_text(
            f"""---
{ftext}
---
{row['INSTNM']}"""
        )

if __name__ == "__main__":
    app()
