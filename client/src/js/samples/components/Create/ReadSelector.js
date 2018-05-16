/**
 * @license
 * The MIT License (MIT)
 * Copyright 2015 Government of Canada
 *
 * @author
 * Ian Boyes
 *
 * @exports ReadSelector
 */
import React from "react";
import { filter, includes, intersection, map, sortBy, toLower, without} from "lodash-es";
import PropTypes from "prop-types";
import { Panel, FormGroup, InputGroup } from "react-bootstrap";
import { Link } from "react-router-dom";

import ReadItem from "./ReadItem";
import { Icon, Input, Button, ListGroupItem } from "../../../base";


export default class ReadSelector extends React.PureComponent {

    constructor (props) {
        super(props);
        this.state = {
            filter: ""
        };
    }

    static propTypes = {
        files: PropTypes.arrayOf(PropTypes.object),
        error: PropTypes.string,
        selected: PropTypes.arrayOf(PropTypes.string),
        onSelect: PropTypes.func
    };

    componentDidUpdate (prevProps) {
        if (this.props.files !== prevProps.files) {
            prevProps.onSelect(intersection(prevProps.selected, map(this.props.files, "id")));
        }
    }

    onSelect = (selectedId) => {
        let selected;

        if (includes(this.props.selected, selectedId)) {
            selected = without(this.props.selected, selectedId);
        } else {
            selected = this.props.selected.concat([selectedId]);

            if (selected.length === 3) {
                selected.shift();
            }
        }

        this.props.onSelect(selected);
    };

    reset = (e) => {
        e.preventDefault();
        this.setState({filter: ""}, () => this.props.onSelect([]));
    };

    render () {

        const error = this.props.error;

        const loweredFilter = toLower(this.state.filter);

        const files = filter(this.props.files, file =>
            !this.state.filter || includes(toLower(file.name), loweredFilter)
        );

        let fileComponents = map(sortBy(files, "uploaded_at").reverse(), file =>
            <ReadItem
                key={file.id}
                {...file}
                selected={includes(this.props.selected, file.id)}
                onSelect={this.onSelect}
            />
        );

        if (!fileComponents.length) {
            fileComponents = (
                <ListGroupItem className="text-center">
                    <Icon name="info" /> No read files found. <Link to="samples/files">Upload some</Link>.
                </ListGroupItem>
            );
        }

        const inputErrorClassName = error ? "input-form-error" : "input-form-error-none";

        const errorMessage = (
            <div className={inputErrorClassName}>
                {error ? error : "None"}
            </div>
        );

        return (
            <div>
                <h5 style={{display: "flex", alignItems: "center"}}>
                    <strong style={{flex: "1 0 auto"}}>Read Files</strong>
                    <small className="text-muted pull-right">
                        {this.props.selected.length} of {fileComponents.length} selected
                    </small>
                </h5>

                <Panel bsStyle={error ? "danger" : "default"} ref={(node) => this.panelNode = node}>
                    <Panel.Body>
                        <div className="toolbar">
                            <FormGroup>
                                <InputGroup>
                                    <Input
                                        type="text"
                                        placeholder="Filename"
                                        value={this.state.filter}
                                        onChange={(e) => this.setState({filter: e.target.value})}
                                    />
                                    <InputGroup.Button>
                                        <Button type="button" tip="Clear" onClick={this.reset}>
                                            <Icon name="reset" />
                                        </Button>
                                    </InputGroup.Button>
                                </InputGroup>
                            </FormGroup>
                        </div>

                        <div style={{maxHeight: "400px", overflowY: "auto"}}>
                            <div className="list-group" style={{border: "none", marginBottom: 0}}>
                                {fileComponents}
                            </div>
                        </div>

                        {errorMessage}
                    </Panel.Body>
                </Panel>
            </div>
        );
    }
}
