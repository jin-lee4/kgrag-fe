import Toggle from "./Toggle";

const Mode = ({ count, title, description, bgColor, toggleColor }) => {


  return (
    <div className="flex items-start justify-between border-b py-4 border-gray-200 w-full">
      <div
        className={`flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full text-white font-bold`}
        style={{ backgroundColor: bgColor }}
      >
        <h3>{count}</h3>
      </div>
      <div className="ml-4 flex-grow">
        <div className="flex justify-between items-center">
          <h3>{title}</h3>
          <Toggle toggleColor={toggleColor} className="items-end"/>
        </div>
        <p className="mt-2 text-xs">{description}</p>
      </div>
    </div>
  );
};

export default Mode;
