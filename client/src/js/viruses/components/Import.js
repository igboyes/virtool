import React from "react";
import PropTypes from "prop-types";
import Dropzone from "react-dropzone";
import { connect } from "react-redux";
import { Modal, Panel, Table, ProgressBar } from "react-bootstrap";
import { Button, RelativeTime } from "../../base";
import { uploadImport, commitImport } from "../actions";


const getInitialState = () => ({
    uploadProgress: 0
});

class VirusImport extends React.Component {

    constructor (props) {
        super(props);
        this.state = getInitialState();
    }

    static propTypes = {
        show: PropTypes.bool,
        onHide: PropTypes.func,
        importData: PropTypes.object,
        onDrop: PropTypes.func,
        onCommit: PropTypes.func
    };

    handleProgress = (progressEvent) => {
        this.setState({uploadProgress: progressEvent.loaded / progressEvent.total});
    };

    handleCommit = () => {
        this.props.onCommit(this.props.importData.file_id);
    };

    render () {
        let body;
        let footer;

        if (this.props.importData === null) {
            body = (
                <div>
                    <Dropzone className="dropzone" onDrop={files => this.props.onDrop(files[0], this.handleProgress)}>
                        <span>Drag or click here to upload a <strong>viruses.json.gz</strong> file.</span>
                    </Dropzone>

                    <p className="text-center small">
                        {this.state.uploadProgress}
                    </p>
                </div>
            );
        } else {
            const data = this.props.importData;

            if (data.duplicates || data.errors) {
                body = <strong>The import file is invalid.</strong>;
            } else {
                let progress;

                if (data.inProgress) {
                    progress = (
                        <Panel>
                            <ProgressBar now={data.inserted || 0 / data.totals.viruses * 100} />
                            <p className="text-center text-muted">
                                <small>Inserted {data.inserted} of {data.totals.viruses}</small>
                            </p>
                        </Panel>
                    );
                }

                body = (
                    <div>
                        {progress}

                        <Table bordered>
                            <tbody>
                                <tr>
                                    <th>Created</th>
                                    <td><RelativeTime time={data.file_created_at} /></td>
                                </tr>
                                <tr>
                                    <th>Version</th>
                                    <td>{data.version || "None"}</td>
                                </tr>
                                <tr>
                                    <th>Viruses</th>
                                    <td>{data.totals.viruses}</td>
                                </tr>
                                <tr>
                                    <th>Isolates</th>
                                    <td>{data.totals.isolates}</td>
                                </tr>
                                <tr>
                                    <th>Sequences</th>
                                    <td>{data.totals.sequences}</td>
                                </tr>
                            </tbody>
                        </Table>
                    </div>
                );

                footer = (
                    <Modal.Footer>
                        <Button bsStyle="primary" icon="checkmark" onClick={this.handleCommit} pullRight>
                            Import
                        </Button>
                    </Modal.Footer>
                );
            }
        }

        return (
            <Modal show={this.props.show} onHide={this.props.onHide}>
                <Modal.Header onHide={this.props.onHide} closeButton>
                    Import Viruses
                </Modal.Header>

                <Modal.Body>
                    {body}
                </Modal.Body>

                {footer}
            </Modal>
        );
    }

}

const mapStateToProps = state => ({
    importData: state.viruses.importData
});

const mapDispatchToProps = dispatch => ({

    onDrop: (file, onProgress) => {
        dispatch(uploadImport(file, onProgress));
    },

    onCommit: (fileId) => {
        dispatch(commitImport(fileId));
    }

});

const Container = connect(mapStateToProps, mapDispatchToProps)(VirusImport);

export default Container;


