import ReadSelector from "../ReadSelector";

describe("<ReadSelector />", () => {
    let props;

    beforeEach(() => {
        props = {
            files: [{ id: "foo", size: 1024, name: "bar" }],
            error: "foo",
            selected: ["foo", "bar"],
            onSelect: jest.fn(),
            handleSelect: jest.fn()
        };
    });

    it("should render", () => {
        const wrapper = shallow(<ReadSelector {...props} />);
        expect(wrapper).toMatchSnapshot();
    });

    it("componentDidUpdate should not call onChange() if props.file does not change ", () => {
        expect(props.onSelect).not.toHaveBeenCalled();
    });

    it("componentDidUpdate should call onChange() if props.file changes ", () => {
        const wrapper = shallow(<ReadSelector {...props} />);
        wrapper.setProps({
            files: [{ id: "Foo", size: 2048, name: "Bar" }],
            error: "foo",
            selected: ["foo", "bar"],
            onSelect: jest.fn(),
            handleSelect: jest.fn(),
            state: {
                filter: "foo"
            }
        });
        expect(props.onSelect).toHaveBeenCalled();
    });

    it("should change state when Input onChange is called", () => {
        const wrapper = shallow(<ReadSelector {...props} />);
        const e = {
            target: {
                value: "Baz"
            }
        };
        wrapper.find("Input").simulate("change", e);
        expect(wrapper.state()).toEqual({ filter: "Baz" });
    });

    it("should call reset when reset Button is clicked", () => {
        const wrapper = shallow(<ReadSelector {...props} />);
        const e = {
            preventDefault: jest.fn()
        };
        wrapper
            .find("Button")
            .at(0)
            .simulate("click", e);
        expect(wrapper.state()).toEqual({ filter: "" });
        expect(props.onSelect).toHaveBeenCalledWith([]);
    });

    it("should call reset when swap Button is clicked", () => {
        const wrapper = shallow(<ReadSelector {...props} />);
        wrapper
            .find("Button")
            .at(1)
            .simulate("click");
        expect(props.onSelect).toHaveBeenCalledWith(["bar", "foo"]);
    });
});
