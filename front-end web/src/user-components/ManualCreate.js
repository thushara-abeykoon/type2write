import React from "react";
import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { FiUpload } from "react-icons/fi";
import { IoIosCloseCircle } from "react-icons/io";

export default function ManualCreate() {
  const [characterFiles, setCharacterFiles] = useState([]);
  const { getRootProps, getInputProps } = useDropzone({
    onDrop: (acceptedFiles) => {
      setCharacterFiles(acceptedFiles);
    },
  });
  const characters = Array.from({ length: 10 }, (_, i) =>
    String.fromCharCode(48 + i)
  )
    .concat(Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i)))
    .concat(Array.from({ length: 26 }, (_, i) => String.fromCharCode(97 + i)));

  const [alertBoxVisible, setAlertBoxVisible] = useState(true);

  return (
    <div className="w-full flex flex-col items-center mx-10">
      {alertBoxVisible ? (
        <div className="w-full bg-red-300 bg-opacity-50 backdrop-blur-md font-mono px-10 py-3 rounded-lg text-red-900 mb-5 flex justify-between items-center">
          <div className="flex items-center gap-10">
            <p className="text-3xl font-bold">ALERT!</p>
            <p className="w-3/4">
              If you going to upload a folder containing the character images,
              Be sure each image is named correctly, like A.jpg, b.png, and so
              on. It's super important for things to work smoothly!
            </p>
          </div>
          <IoIosCloseCircle
            className="text-5xl cursor-pointer"
            onClick={() => {
              setAlertBoxVisible(false);
            }}
          />
        </div>
      ) : (
        <></>
      )}
      <div
        {...getRootProps()}
        className="cursor-pointer h-96 bg-orange-700 bg-opacity-80 backdrop-blur-md text-white px-10 py-5 flex flex-col justify-around items-center w-full mb-10 rounded-xl text-3xl font-mono"
      >
        <FiUpload className="text-8xl" />
        <input {...getInputProps()} />
        <p>Click Or Drop to Upload the Image Folder Here....</p>
      </div>
      <div className="grid grid-cols-4 w-full gap-10 mb-10">
        {characters.map((chr) => (
          <CharacterUploadBox key={chr} character={chr} />
        ))}
      </div>
    </div>
  );
}

function CharacterUploadBox({ character }) {
  const [file, setFile] = useState(null);

  const onDrop = (acceptedFile) => {
    setFile(acceptedFile);
  };
  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    multiple: false,
  });
  return (
    <div
      {...getRootProps()}
      className="backdrop-blur-sm w-full cursor-pointer hover:bg-teal-700 transition-colors duration-200 h-96 flex justify-between items-center font-mono  rounded-xl hover:text-white text-5xl text-teal-700 flex-col"
    >
      {file !== null ? (
        <img
          src={URL.createObjectURL(file[0])}
          className="w-full h-3/4 border-4 border-teal-700 rounded-t-xl"
        />
      ) : (
        <>
          <input {...getInputProps()} />
          <div className=" px-5 border-dashed border-t-4 border-x-4 border-teal-700 rounded-t-xl h-3/4 flex flex-col justify-center gap-6 items-center w-full text-center text-2xl">
            <FiUpload className="text-5xl" />
            <p>Click or Drop Here to Upload Image</p>
          </div>
        </>
      )}
      <div className="h-1/4 rounded-b-xl flex justify-center items-center w-full bg-teal-700 text-white">
        {character}
      </div>
    </div>
  );
}
