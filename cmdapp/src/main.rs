mod config;
mod converter;
mod svg;

use clap::{App, Arg};
use config::{ColorMode, Config, Hierarchical, OutputFormat, Preset};
use std::fs;
use std::path::{Path, PathBuf};
use std::str::FromStr;
use visioncortex::PathSimplifyMode;

fn path_simplify_mode_from_str(s: &str) -> PathSimplifyMode {
    match s {
        "polygon" => PathSimplifyMode::Polygon,
        "spline" => PathSimplifyMode::Spline,
        "none" => PathSimplifyMode::None,
        _ => panic!("unknown PathSimplifyMode {}", s),
    }
}

pub fn config_from_args() -> (PathBuf, PathBuf, Config, OutputFormat) {
    let app = App::new("visioncortex VTracer ".to_owned() + env!("CARGO_PKG_VERSION"))
        .about("A cmd app to convert images into vector graphics.");

    let app = app.arg(
        Arg::with_name("input")
            .long("input")
            .short("i")
            .takes_value(true)
            .help("Path to input raster image")
            .required(true),
    );

    let app = app.arg(
        Arg::with_name("output")
            .long("output")
            .short("o")
            .takes_value(true)
            .help("Path to output vector graphics")
            .required(true),
    );

    let app = app.arg(
        Arg::with_name("color_mode")
            .long("colormode")
            .takes_value(true)
            .help("True color image `color` (default) or Binary image `bw`"),
    );

    let app = app.arg(
        Arg::with_name("hierarchical")
            .long("hierarchical")
            .takes_value(true)
            .help(
                "Hierarchical clustering `stacked` (default) or non-stacked `cutout`. \
            Only applies to color mode. ",
            ),
    );

    let app = app.arg(
        Arg::with_name("preset")
            .long("preset")
            .takes_value(true)
            .help("Use one of the preset configs `bw`, `poster`, `photo`"),
    );

    let app = app.arg(
        Arg::with_name("filter_speckle")
            .long("filter_speckle")
            .short("f")
            .takes_value(true)
            .help("Discard patches smaller than X px in size"),
    );

    let app = app.arg(
        Arg::with_name("color_precision")
            .long("color_precision")
            .short("p")
            .takes_value(true)
            .help("Number of significant bits to use in an RGB channel"),
    );

    let app = app.arg(
        Arg::with_name("gradient_step")
            .long("gradient_step")
            .short("g")
            .takes_value(true)
            .help("Color difference between gradient layers"),
    );

    let app = app.arg(
        Arg::with_name("corner_threshold")
            .long("corner_threshold")
            .short("c")
            .takes_value(true)
            .help("Minimum momentary angle (degree) to be considered a corner"),
    );

    let app = app.arg(Arg::with_name("segment_length")
        .long("segment_length")
        .short("l")
        .takes_value(true)
        .help("Perform iterative subdivide smooth until all segments are shorter than this length"));

    let app = app.arg(
        Arg::with_name("splice_threshold")
            .long("splice_threshold")
            .short("s")
            .takes_value(true)
            .help("Minimum angle displacement (degree) to splice a spline"),
    );

    let app = app.arg(
        Arg::with_name("mode")
            .long("mode")
            .short("m")
            .takes_value(true)
            .help("Curver fitting mode `pixel`, `polygon`, `spline`"),
    );

    let app = app.arg(
        Arg::with_name("path_precision")
            .long("path_precision")
            .takes_value(true)
            .help("Number of decimal places to use in path string"),
    );

    let app = app.arg(
        Arg::with_name("stroke_width")
            .long("stroke_width")
            .takes_value(true)
            .help("Outline stroke width in points (e.g., 1, 2, 3)"),
    );

    let app = app.arg(
        Arg::with_name("stroke_color")
            .long("stroke_color")
            .takes_value(true)
            .help("Outline stroke color (e.g., black, #000000, rgb(0,0,0))"),
    );

    let app = app.arg(
        Arg::with_name("format")
            .long("format")
            .short("t")
            .takes_value(true)
            .help("Output format: svg (default), png, ai"),
    );

    // Extract matches
    let matches = app.get_matches();

    let mut config = Config::default();
    let input_path = matches
        .value_of("input")
        .expect("Input path is required, please specify it by --input or -i.");
    let output_path = matches
        .value_of("output")
        .expect("Output path is required, please specify it by --output or -o.");

    let input_path = PathBuf::from(input_path);
    let output_path = PathBuf::from(output_path);

    if let Some(value) = matches.value_of("preset") {
        config = Config::from_preset(Preset::from_str(value).unwrap());
    }

    if let Some(value) = matches.value_of("color_mode") {
        config.color_mode = ColorMode::from_str(if value.trim() == "bw" || value.trim() == "BW" {
            "binary"
        } else {
            "color"
        })
        .unwrap()
    }

    if let Some(value) = matches.value_of("hierarchical") {
        config.hierarchical = Hierarchical::from_str(value).unwrap()
    }

    if let Some(value) = matches.value_of("mode") {
        let value = value.trim();
        config.mode = path_simplify_mode_from_str(if value == "pixel" {
            "none"
        } else if value == "polygon" {
            "polygon"
        } else if value == "spline" {
            "spline"
        } else {
            panic!("Parser Error: Curve fitting mode is invalid: {}", value);
        });
    }

    if let Some(value) = matches.value_of("filter_speckle") {
        if value.trim().parse::<usize>().is_ok() {
            // is numeric
            let value = value.trim().parse::<usize>().unwrap();
            if value > 16 {
                panic!("Out of Range Error: Filter speckle is invalid at {}. It must be within [0,16].", value);
            }
            config.filter_speckle = value;
        } else {
            panic!(
                "Parser Error: Filter speckle is not a positive integer: {}.",
                value
            );
        }
    }

    if let Some(value) = matches.value_of("color_precision") {
        if value.trim().parse::<i32>().is_ok() {
            // is numeric
            let value = value.trim().parse::<i32>().unwrap();
            if value < 1 || value > 8 {
                panic!("Out of Range Error: Color precision is invalid at {}. It must be within [1,8].", value);
            }
            config.color_precision = value;
        } else {
            panic!(
                "Parser Error: Color precision is not an integer: {}.",
                value
            );
        }
    }

    if let Some(value) = matches.value_of("gradient_step") {
        if value.trim().parse::<i32>().is_ok() {
            // is numeric
            let value = value.trim().parse::<i32>().unwrap();
            if value < 0 || value > 255 {
                panic!("Out of Range Error: Gradient step is invalid at {}. It must be within [0,255].", value);
            }
            config.layer_difference = value;
        } else {
            panic!("Parser Error: Gradient step is not an integer: {}.", value);
        }
    }

    if let Some(value) = matches.value_of("corner_threshold") {
        if value.trim().parse::<i32>().is_ok() {
            // is numeric
            let value = value.trim().parse::<i32>().unwrap();
            if value < 0 || value > 180 {
                panic!("Out of Range Error: Corner threshold is invalid at {}. It must be within [0,180].", value);
            }
            config.corner_threshold = value
        } else {
            panic!("Parser Error: Corner threshold is not numeric: {}.", value);
        }
    }

    if let Some(value) = matches.value_of("segment_length") {
        if value.trim().parse::<f64>().is_ok() {
            // is numeric
            let value = value.trim().parse::<f64>().unwrap();
            if value < 3.5 || value > 10.0 {
                panic!("Out of Range Error: Segment length is invalid at {}. It must be within [3.5,10].", value);
            }
            config.length_threshold = value;
        } else {
            panic!("Parser Error: Segment length is not numeric: {}.", value);
        }
    }

    if let Some(value) = matches.value_of("splice_threshold") {
        if value.trim().parse::<i32>().is_ok() {
            // is numeric
            let value = value.trim().parse::<i32>().unwrap();
            if value < 0 || value > 180 {
                panic!("Out of Range Error: Segment length is invalid at {}. It must be within [0,180].", value);
            }
            config.splice_threshold = value;
        } else {
            panic!("Parser Error: Segment length is not numeric: {}.", value);
        }
    }

    if let Some(value) = matches.value_of("path_precision") {
        if value.trim().parse::<u32>().is_ok() {
            // is numeric
            let value = value.trim().parse::<u32>().ok();
            config.path_precision = value;
        } else {
            panic!(
                "Parser Error: Path precision is not an unsigned integer: {}.",
                value
            );
        }
    }

    if let Some(value) = matches.value_of("stroke_width") {
        if value.trim().parse::<f64>().is_ok() {
            // is numeric
            let value = value.trim().parse::<f64>().unwrap();
            if value < 0.0 {
                panic!("Out of Range Error: Stroke width must be positive: {}.", value);
            }
            config.stroke_width = Some(value);
        } else {
            panic!("Parser Error: Stroke width is not numeric: {}.", value);
        }
    }

    if let Some(value) = matches.value_of("stroke_color") {
        let value = value.trim();
        if !value.is_empty() {
            config.stroke_color = Some(value.to_string());
        }
    }

    // Parse output format
    let output_format = matches
        .value_of("format")
        .map(|f| OutputFormat::from_str(f).unwrap())
        .unwrap_or(OutputFormat::Svg);

    (input_path, output_path, config, output_format)
}

fn run_conversion(
    input_path: &Path,
    output_path: &Path,
    config: Config,
    output_format: &OutputFormat,
) -> Result<(), String> {
    match output_format {
        OutputFormat::Svg => converter::convert_image_to_svg(input_path, output_path, config),
        OutputFormat::Png => converter::convert_image_to_png(input_path, output_path, config),
        OutputFormat::Ai => converter::convert_image_to_ai(input_path, output_path, config),
    }
}

fn supported_input_file(path: &Path) -> bool {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| matches!(
            ext.to_ascii_lowercase().as_str(),
            "png" | "jpg" | "jpeg" | "bmp" | "gif" | "ai"
        ))
        .unwrap_or(false)
}

fn output_extension(output_format: &OutputFormat) -> &'static str {
    match output_format {
        OutputFormat::Svg => "svg",
        OutputFormat::Png => "png",
        OutputFormat::Ai => "ai",
    }
}

fn unique_output_path(output_dir: &Path, file_stem: &str, output_format: &OutputFormat) -> PathBuf {
    let extension = output_extension(output_format);
    let preferred = output_dir.join(format!("{}.{}", file_stem, extension));
    if !preferred.exists() {
        return preferred;
    }

    let mut index = 2usize;
    loop {
        let candidate = output_dir.join(format!("{}-{}.{}", file_stem, index, extension));
        if !candidate.exists() {
            return candidate;
        }
        index += 1;
    }
}

fn convert_directory(
    input_dir: &Path,
    output_dir: &Path,
    config: Config,
    output_format: &OutputFormat,
) -> Result<(), String> {
    if !output_dir.exists() {
        return Err(format!(
            "Output directory '{}' does not exist",
            output_dir.display()
        ));
    }
    if !output_dir.is_dir() {
        return Err(format!(
            "Output path '{}' is not a directory",
            output_dir.display()
        ));
    }

    let entries = fs::read_dir(input_dir)
        .map_err(|err| format!("Failed to read input directory '{}': {}", input_dir.display(), err))?;

    let mut files = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|err| {
            format!(
                "Failed to enumerate input directory '{}': {}",
                input_dir.display(),
                err
            )
        })?;
        let path = entry.path();
        if path.is_file() && supported_input_file(&path) {
            files.push(path);
        }
    }

    files.sort();

    if files.is_empty() {
        return Err(format!(
            "No supported input files found in '{}'. Supported formats: png, jpg, jpeg, bmp, gif, ai",
            input_dir.display()
        ));
    }

    let mut success_count = 0usize;
    let mut failure_count = 0usize;

    for input_file in files {
        let file_stem = match input_file.file_stem().and_then(|stem| stem.to_str()) {
            Some(stem) if !stem.is_empty() => stem,
            _ => {
                failure_count += 1;
                eprintln!("Skipping '{}': invalid file name", input_file.display());
                continue;
            }
        };

        let output_file = unique_output_path(output_dir, file_stem, output_format);
        match run_conversion(&input_file, &output_file, config.clone(), output_format) {
            Ok(()) => {
                success_count += 1;
                println!("Converted '{}' -> '{}'", input_file.display(), output_file.display());
            }
            Err(err) => {
                failure_count += 1;
                eprintln!("Failed '{}' -> '{}': {}", input_file.display(), output_file.display(), err);
            }
        }
    }

    println!(
        "Batch conversion finished: {} succeeded, {} failed.",
        success_count, failure_count
    );

    if success_count == 0 {
        return Err(String::from("Batch conversion failed for all supported files"));
    }

    Ok(())
}

fn main() {
    let (input_path, output_path, config, output_format) = config_from_args();
    let result = if input_path.is_dir() {
        convert_directory(&input_path, &output_path, config, &output_format)
    } else {
        run_conversion(&input_path, &output_path, config, &output_format)
    };
    match result {
        Ok(()) => {
            println!("Conversion successful.");
        }
        Err(msg) => {
            panic!("Conversion failed with error message: {}", msg);
        }
    }
}
