import React from "react";
import { Flex, FlexItem } from "virtool/js/components/Base";
import { toScientificNotation } from "virtool/js/utils";
import Coverage from "./Coverage";

export default class PathoscopeIsolate extends React.Component {

    static propTypes = {
        virusId: React.PropTypes.string,
        name: React.PropTypes.string,

        pi: React.PropTypes.number,
        best: React.PropTypes.number,
        coverage: React.PropTypes.number,
        maxDepth: React.PropTypes.number,
        reads: React.PropTypes.number,

        hits: React.PropTypes.arrayOf(React.PropTypes.object),

        setScroll: React.PropTypes.func,
        showReads: React.PropTypes.bool
    };

    componentDidMount () {
        this.refs.chartNode.addEventListener("scroll", this.handleScroll);
    }

    componentWillUnmount () {
        this.refs.chartNode.removeEventListener("scroll", this.handleScroll);
    }

    scrollTo = (scrollLeft) => {
        this.refs.chartNode.scrollLeft = scrollLeft;
    };

    handleScroll = (event) => {
        this.props.setScroll(this.props.virusId, event.target.scrollLeft);
    };

    render () {

        const chartContainerStyle = {
            overflowX: "scroll",
            whiteSpace: "nowrap"
        };

        const sorted = this.props.hits.sort(hit => hit.align.length);

        const hitComponents = sorted.map((hit, index) => (
            <Coverage
                key={hit.accession}
                data={hit.align}
                accession={hit.accession}
                definition={hit.definition}
                yMax={this.props.maxDepth}
                showYAxis={index === hitComponents.length - 1}
                isolateComponent={this}
            />
        ));

        const piValue = this.props.showReads ? this.props.reads: toScientificNotation(this.props.pi);

        return (
            <div>
                <div className="pathoscope-isolate-header">
                    <Flex>
                        <FlexItem>
                            {this.props.name}
                        </FlexItem>
                        <FlexItem pad={5}>
                            <strong className="small text-success">
                                {piValue}
                            </strong>
                        </FlexItem>
                        <FlexItem pad={5}>
                            <strong className="small text-danger">
                                {toScientificNotation(this.props.best)}
                            </strong>
                        </FlexItem>
                        <FlexItem pad={5}>
                            <strong className="small text-primary">
                                {toScientificNotation(this.props.coverage)}
                            </strong>
                        </FlexItem>
                    </Flex>
                </div>
                <div ref={this.chartNode} style={chartContainerStyle}>
                    {hitComponents}
                </div>
            </div>
        );
    }
}
