import { map } from "lodash-es";
import Moment from "moment";
import numbro from "numbro";
import React, { useCallback } from "react";
import { Panel } from "react-bootstrap";
import { connect } from "react-redux";
import styled from "styled-components";
import { Button, Flex, FlexItem, Icon, InfoAlert, Loader, RelativeTime, Table } from "../../../base";

import { blastNuvs } from "../../actions";

const ridRoot =
    "https://blast.ncbi.nlm.nih.gov/Blast.cgi?\
    CMD=Web&PAGE_TYPE=BlastFormatting&OLD_BLAST=false&GET_RID_INFO=on&RID=";

export const BLASTButton = styled(Button)`
    margin-left: auto;
`;

export const BLASTInProgress = ({ interval, lastCheckedAt, rid }) => {
    let timing;
    let ridText;
    let ridLink;

    if (rid) {
        const relativeLast = <RelativeTime time={lastCheckedAt} />;
        const relativeNext = Moment(lastCheckedAt)
            .add(interval, "seconds")
            .fromNow();

        ridText = " with RID ";

        ridLink = (
            <a target="_blank" href={ridRoot + rid} rel="noopener noreferrer">
                {rid}{" "}
                <sup>
                    <Icon name="new-tab" />
                </sup>
            </a>
        );

        timing = (
            <FlexItem grow={1}>
                <small className="pull-right">
                    Last checked {relativeLast}. Checking again in {relativeNext}.
                </small>
            </FlexItem>
        );
    }

    return (
        <Panel>
            <Panel.Body>
                <Flex alignItems="center">
                    <FlexItem>
                        <Loader size={16} color="#000" />
                    </FlexItem>
                    <FlexItem pad={5}>
                        <span>BLAST in progress {ridText}</span>
                        {ridLink}
                    </FlexItem>
                    {timing}
                </Flex>
            </Panel.Body>
        </Panel>
    );
};

export const BLASTResults = ({ hits }) => {
    const components = map(hits, (hit, index) => (
        <tr key={index}>
            <td>
                <a
                    target="_blank"
                    href={`https://www.ncbi.nlm.nih.gov/nuccore/${hit.accession}`}
                    rel="noopener noreferrer"
                >
                    {hit.accession}
                </a>
            </td>
            <td>{hit.name}</td>
            <td>{hit.evalue}</td>
            <td>{hit.score}</td>
            <td>{numbro(hit.identity / hit.align_len).format("0.00")}</td>
        </tr>
    ));

    return (
        <Panel>
            <Panel.Heading>NCBI BLAST</Panel.Heading>
            <Panel.Body>
                <Table>
                    <thead>
                        <tr>
                            <th>Accession</th>
                            <th>Name</th>
                            <th>E-value</th>
                            <th>Score</th>
                            <th>Identity</th>
                        </tr>
                    </thead>
                    <tbody>{components}</tbody>
                </Table>
            </Panel.Body>
        </Panel>
    );
};

export const NuVsBLAST = ({ analysisId, blast, sequenceIndex, onBlast }) => {
    const handleBlast = useCallback(() => onBlast(analysisId, sequenceIndex), [analysisId, sequenceIndex]);

    if (blast) {
        if (blast.ready) {
            if (blast.result.hits.length) {
                return <BLASTResults hits={blast.result.hits} />;
            }

            return (
                <Panel>
                    <Panel.Heading>NCBI BLAST</Panel.Heading>
                    <Panel.Body>No BLAST hits found.</Panel.Body>
                </Panel>
            );
        }

        return <BLASTInProgress interval={blast.interval} lastCheckedAt={blast.last_checked_at} rid={blast.rid} />;
    }

    return (
        <InfoAlert level>
            <Icon name="info-circle" />
            <span>This sequence has no BLAST information attached to it.</span>
            <BLASTButton bsSize="small" icon="cloud" onClick={handleBlast}>
                BLAST at NCBI
            </BLASTButton>
        </InfoAlert>
    );
};

const mapStateToProps = state => ({
    analysisId: state.analyses.detail.id
});

const mapDispatchToProps = dispatch => ({
    onBlast: (analysisId, sequenceIndex) => {
        dispatch(blastNuvs(analysisId, sequenceIndex));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(NuVsBLAST);
