import React from "react";
import { connect } from "react-redux";
import { push } from "react-router-redux";
import { Link } from "react-router-dom";
import { find } from "lodash-es";
import { RelativeTime, ProgressBar, Icon } from "../../base";
import { Panel, Table, Row, ListGroup } from "react-bootstrap";

const ReferenceHeader = ({ name, createdAt, user, refId }) => (
    <div style={{ marginLeft: "5px" }}>
        <Row>
            <strong>{name}</strong>
            <Link to={{state: {newReference: true, cloneReference: true, refId}}} style={{float: "right"}}>
                <Icon name="clone" bsStyle="warning" tip="Clone Reference" />
            </Link>
        </Row>
        <Row>
            <small>
                Created <RelativeTime time={createdAt} /> by {user}
            </small>
        </Row>
    </div>
);

const ReferenceMetadata = ({ data_type, organism }) => (
    <Table bordered>
        <tbody>
            <tr>
                <th>Data Type</th>
                <td className="text-capitalize">
                    {data_type}
                </td>
            </tr>
            <tr>
                <th>Organism</th>
                <td className="text-capitalize">
                    {organism || "unknown"}
                </td>
            </tr>
        </tbody>
    </Table>
);

const ReferenceItem = (props) => {

    let progress = 0;
    let step;

    if (props.process && props.processes.length) {
        const process = find(props.processes, ["id", props.process.id]);
        progress = process.progress;
        step = process.step;
        progress *= 100;
    } else {
        step = "None";
        progress = 100;
    }

    return (
        <Panel className="reference-item" onClick={props.onClick}>
            <Panel.Heading>
                <ReferenceHeader name={props.name} createdAt={props.created_at} user={props.user.id} refId={props.id} />
            </Panel.Heading>

            <ReferenceMetadata {...props} />
            <Panel.Body style={{padding: 0, textAlign: "center"}}>
                <span style={{visibility: `${progress === 100 ? "hidden" : "visible"}`, fontSize: "small"}}>
                    {step}
                </span>
            </Panel.Body>
            <ListGroup>
                <ProgressBar
                    bsStyle={progress === 100 ? "success" : "warning"}
                    now={progress}
                    affixed
                />
            </ListGroup>
        </Panel>
    );
};

const mapStateToProps = state => ({
    processes: state.processes.documents
});

const mapDispatchToProps = (dispatch, ownProps) => ({
    onClick: (e) => {
        if (e.target.nodeName !== "I") {
            dispatch(push(`/refs/${ownProps.id}`));
        }
    }
});

export default connect(mapStateToProps, mapDispatchToProps)(ReferenceItem);
