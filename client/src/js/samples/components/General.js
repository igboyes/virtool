import numbro from "numbro";
import React from "react";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import styled from "styled-components";
import { BoxGroup, BoxGroupHeader, Table } from "../../base";
import EditSample from "./Edit";
import SampleFileSizeWarning from "./SampleFileSizeWarning.js";

const libraryTypes = {
    normal: "Normal",
    srna: "sRNA",
    amplicon: "Amplicon"
};

const StyledSampleDetailGeneral = styled.div`
    th {
        width: 220px;
    }
`;

export const SampleDetailGeneral = ({
    count,
    encoding,
    gc,
    host,
    isolate,
    lengthRange,
    locale,
    name,
    paired,
    subtraction,
    libraryType
}) => (
    <StyledSampleDetailGeneral>
        <SampleFileSizeWarning />
        <BoxGroup>
            <BoxGroupHeader>
                <h2>General</h2>
                <p>User-defined information about the sample.</p>
            </BoxGroupHeader>
            <Table>
                <tbody>
                    <tr>
                        <th>Name</th>
                        <td>{name}</td>
                    </tr>
                    <tr>
                        <th>Host</th>
                        <td>{host}</td>
                    </tr>
                    <tr>
                        <th>Isolate</th>
                        <td>{isolate}</td>
                    </tr>
                    <tr>
                        <th>Locale</th>
                        <td>{locale}</td>
                    </tr>
                </tbody>
            </Table>
        </BoxGroup>

        <BoxGroup>
            <BoxGroupHeader>
                <h2>Library</h2>
                <p>Information about the sequencing reads in this sample.</p>
            </BoxGroupHeader>
            <Table>
                <tbody>
                    <tr>
                        <th>Encoding</th>
                        <td>{encoding}</td>
                    </tr>
                    <tr>
                        <th>Read Count</th>
                        <td>{count}</td>
                    </tr>
                    <tr>
                        <th>Library Type</th>
                        <td>{libraryType}</td>
                    </tr>
                    <tr>
                        <th>Length Range</th>
                        <td>{lengthRange}</td>
                    </tr>
                    <tr>
                        <th>GC Content</th>
                        <td>{gc}</td>
                    </tr>
                    <tr>
                        <th>Paired</th>
                        <td>{paired ? "Yes" : "No"}</td>
                    </tr>
                </tbody>
            </Table>
        </BoxGroup>

        <BoxGroup>
            <BoxGroupHeader>
                <h2>Default Subtraction</h2>
                <p>This subtraction will be the default selection when creating an analysis.</p>
            </BoxGroupHeader>
            <Table>
                <tbody>
                    <tr>
                        <th>Subtraction</th>
                        <td>
                            <Link to={`/subtraction/${subtraction.id}`}>{subtraction.name}</Link>
                        </td>
                    </tr>
                </tbody>
            </Table>
        </BoxGroup>

        <EditSample />
    </StyledSampleDetailGeneral>
);

export const mapStateToProps = state => {
    const { name, host, isolate, locale, paired, quality, library_type, subtraction } = state.samples.detail;
    const { count, encoding, gc, length } = quality;

    return {
        encoding,
        host,
        isolate,
        locale,
        name,
        paired,
        count: numbro(count).format("0.0 a"),
        gc: numbro(gc / 100).format("0.0 %"),
        libraryType: libraryTypes[library_type],
        lengthRange: length.join(" - "),
        subtraction
    };
};

export default connect(mapStateToProps)(SampleDetailGeneral);
