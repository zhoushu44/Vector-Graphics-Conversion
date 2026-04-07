use std::fmt;

use resvg::tiny_skia::{LineCap, LineJoin, PathBuilder, PathSegment, Stroke};
use visioncortex::{Color, CompoundPath, CompoundPathElement, PointF64};

#[derive(Debug, Clone)]
pub struct SvgFile {
    pub paths: Vec<SvgPath>,
    pub width: usize,
    pub height: usize,
    pub path_precision: Option<u32>,
}

#[derive(Debug, Clone)]
pub struct SvgPath {
    pub path: CompoundPath,
    pub color: Color,
    pub stroke_width: Option<f64>,
    pub stroke_color: Option<String>,
    pub expand_stroke: bool,
    pub outer_stroke_only: bool,
}

impl SvgFile {
    pub fn new(width: usize, height: usize, path_precision: Option<u32>) -> Self {
        SvgFile {
            paths: vec![],
            width,
            height,
            path_precision,
        }
    }

    pub fn add_path(
        &mut self,
        path: CompoundPath,
        color: Color,
        stroke_width: Option<f64>,
        stroke_color: Option<String>,
        expand_stroke: bool,
        outer_stroke_only: bool,
    ) {
        self.paths.push(SvgPath {
            path,
            color,
            stroke_width,
            stroke_color,
            expand_stroke,
            outer_stroke_only,
        })
    }
}

impl fmt::Display for SvgFile {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        writeln!(f, r#"<?xml version="1.0" encoding="UTF-8"?>"#)?;
        writeln!(
            f,
            r#"<!-- Generator: visioncortex VTracer {} -->"#,
            env!("CARGO_PKG_VERSION")
        )?;
        writeln!(
            f,
            r#"<svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="{}" height="{}">"#,
            self.width, self.height
        )?;

        for path in &self.paths {
            path.fmt_with_precision(f, self.path_precision)?;
        }

        writeln!(f, "</svg>")
    }
}

impl fmt::Display for SvgPath {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        self.fmt_with_precision(f, None)
    }
}

impl SvgPath {
    fn fmt_with_precision(&self, f: &mut fmt::Formatter, precision: Option<u32>) -> fmt::Result {
        let (fill_path, offset) = self
            .path
            .to_svg_string(true, PointF64::default(), precision);

        match (self.stroke_width, self.expand_stroke, self.outer_stroke_only) {
            (Some(stroke_width), true, false) if stroke_width > 0.0 => {
                self.write_fill_path(f, &fill_path, offset)?;

                if let Some(expanded_path) = self.expanded_stroke_path(precision) {
                    let stroke_color = self.stroke_color.as_deref().unwrap_or("black");
                    writeln!(
                        f,
                        "<path d=\"{}\" fill=\"{}\" fill-rule=\"nonzero\" />",
                        expanded_path,
                        stroke_color
                    )?;
                }
            }
            (Some(stroke_width), false, true) if stroke_width > 0.0 => {
                self.write_fill_path(f, &fill_path, offset)?;

                if let Some(outer_path) = self.outer_stroke_path(precision) {
                    writeln!(
                        f,
                        "<path d=\"{}\" fill=\"none\" stroke-width=\"{:.1}px\" stroke=\"{}\" />",
                        outer_path,
                        stroke_width,
                        self.stroke_color.as_deref().unwrap_or("black")
                    )?;
                }
            }
            (Some(stroke_width), false, false) if stroke_width > 0.0 => {
                writeln!(
                    f,
                    "<path d=\"{}\" fill=\"{}\" transform=\"translate({}, {})\" stroke-width=\"{:.1}px\" stroke=\"{}\" />",
                    fill_path,
                    self.color.to_hex_string(),
                    offset.x,
                    offset.y,
                    stroke_width,
                    self.stroke_color.as_deref().unwrap_or("black")
                )?;
            }
            _ => {
                self.write_fill_path(f, &fill_path, offset)?;
            }
        }

        Ok(())
    }

    fn write_fill_path(
        &self,
        f: &mut fmt::Formatter,
        fill_path: &str,
        offset: PointF64,
    ) -> fmt::Result {
        let fill_attributes = vec![
            format!("d=\"{}\"", fill_path),
            format!("fill=\"{}\"", self.color.to_hex_string()),
            format!("transform=\"translate({}, {})\"", offset.x, offset.y),
        ];
        writeln!(f, "<path {} />", fill_attributes.join(" "))
    }

    fn expanded_stroke_path(&self, precision: Option<u32>) -> Option<String> {
        let path = compound_path_to_tiny_skia_path(&self.path)?;
        let stroked = stroke_compound_path(&path, self.stroke_width?)?;

        Some(tiny_skia_path_to_svg_string(&stroked, precision))
    }

    fn outer_stroke_path(&self, precision: Option<u32>) -> Option<String> {
        let path = compound_path_to_tiny_skia_path(&self.path)?;
        let stroked = stroke_compound_path(&path, self.stroke_width?)?;
        let outer = extract_largest_closed_subpath(&stroked)?;

        Some(subpath_to_svg_string(&outer, precision))
    }
}

fn stroke_compound_path(path: &resvg::tiny_skia::Path, stroke_width: f64) -> Option<resvg::tiny_skia::Path> {
    path.stroke(
        &Stroke {
            width: stroke_width as f32,
            line_cap: LineCap::Round,
            line_join: LineJoin::Round,
            ..Stroke::default()
        },
        1.0,
    )
}

fn compound_path_to_tiny_skia_path(path: &CompoundPath) -> Option<resvg::tiny_skia::Path> {
    let mut builder = PathBuilder::new();

    for element in path.iter() {
        match element {
            CompoundPathElement::PathI32(path) => {
                let closed = path.to_closed();
                if closed.path.is_empty() {
                    continue;
                }

                builder.move_to(closed.path[0].x as f32, closed.path[0].y as f32);
                for point in closed.path.iter().skip(1).take(closed.path.len().saturating_sub(2)) {
                    builder.line_to(point.x as f32, point.y as f32);
                }
                builder.close();
            }
            CompoundPathElement::PathF64(path) => {
                let closed = path.to_closed();
                if closed.path.is_empty() {
                    continue;
                }

                builder.move_to(closed.path[0].x as f32, closed.path[0].y as f32);
                for point in closed.path.iter().skip(1).take(closed.path.len().saturating_sub(2)) {
                    builder.line_to(point.x as f32, point.y as f32);
                }
                builder.close();
            }
            CompoundPathElement::Spline(path) => {
                if path.is_empty() {
                    continue;
                }

                builder.move_to(path.points[0].x as f32, path.points[0].y as f32);
                let mut i = 1;
                while i + 2 < path.points.len() {
                    builder.cubic_to(
                        path.points[i].x as f32,
                        path.points[i].y as f32,
                        path.points[i + 1].x as f32,
                        path.points[i + 1].y as f32,
                        path.points[i + 2].x as f32,
                        path.points[i + 2].y as f32,
                    );
                    i += 3;
                }
                builder.close();
            }
        }
    }

    builder.finish()
}

#[derive(Debug, Clone)]
enum SubpathCommand {
    MoveTo { x: f32, y: f32 },
    LineTo { x: f32, y: f32 },
    QuadTo { cx: f32, cy: f32, x: f32, y: f32 },
    CubicTo {
        c1x: f32,
        c1y: f32,
        c2x: f32,
        c2y: f32,
        x: f32,
        y: f32,
    },
    Close,
}

#[derive(Debug, Clone)]
struct ClosedSubpath {
    commands: Vec<SubpathCommand>,
    sample_points: Vec<(f64, f64)>,
}

impl ClosedSubpath {
    fn bbox_area(&self) -> f64 {
        let mut iter = self.sample_points.iter();
        let Some(&(first_x, first_y)) = iter.next() else {
            return 0.0;
        };

        let (mut min_x, mut max_x) = (first_x, first_x);
        let (mut min_y, mut max_y) = (first_y, first_y);
        for &(x, y) in iter {
            min_x = min_x.min(x);
            max_x = max_x.max(x);
            min_y = min_y.min(y);
            max_y = max_y.max(y);
        }

        (max_x - min_x) * (max_y - min_y)
    }

    fn signed_area(&self) -> f64 {
        if self.sample_points.len() < 3 {
            return 0.0;
        }

        let mut area = 0.0;
        for window in self.sample_points.windows(2) {
            let (x1, y1) = window[0];
            let (x2, y2) = window[1];
            area += x1 * y2 - x2 * y1;
        }

        let (last_x, last_y) = self.sample_points[self.sample_points.len() - 1];
        let (first_x, first_y) = self.sample_points[0];
        area += last_x * first_y - first_x * last_y;
        area * 0.5
    }
}

fn extract_largest_closed_subpath(path: &resvg::tiny_skia::Path) -> Option<ClosedSubpath> {
    let mut subpaths = split_closed_subpaths(path);
    subpaths.sort_by(|a, b| {
        b.bbox_area()
            .partial_cmp(&a.bbox_area())
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| {
                b.signed_area()
                    .abs()
                    .partial_cmp(&a.signed_area().abs())
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    });
    subpaths.into_iter().next()
}

fn split_closed_subpaths(path: &resvg::tiny_skia::Path) -> Vec<ClosedSubpath> {
    let mut subpaths = Vec::new();
    let mut commands = Vec::new();
    let mut sample_points = Vec::new();

    for segment in path.segments() {
        match segment {
            PathSegment::MoveTo(point) => {
                if !commands.is_empty() {
                    commands.clear();
                    sample_points.clear();
                }
                commands.push(SubpathCommand::MoveTo {
                    x: point.x,
                    y: point.y,
                });
                sample_points.push((point.x as f64, point.y as f64));
            }
            PathSegment::LineTo(point) => {
                commands.push(SubpathCommand::LineTo {
                    x: point.x,
                    y: point.y,
                });
                sample_points.push((point.x as f64, point.y as f64));
            }
            PathSegment::QuadTo(control, point) => {
                commands.push(SubpathCommand::QuadTo {
                    cx: control.x,
                    cy: control.y,
                    x: point.x,
                    y: point.y,
                });
                sample_points.push((control.x as f64, control.y as f64));
                sample_points.push((point.x as f64, point.y as f64));
            }
            PathSegment::CubicTo(control1, control2, point) => {
                commands.push(SubpathCommand::CubicTo {
                    c1x: control1.x,
                    c1y: control1.y,
                    c2x: control2.x,
                    c2y: control2.y,
                    x: point.x,
                    y: point.y,
                });
                sample_points.push((control1.x as f64, control1.y as f64));
                sample_points.push((control2.x as f64, control2.y as f64));
                sample_points.push((point.x as f64, point.y as f64));
            }
            PathSegment::Close => {
                commands.push(SubpathCommand::Close);
                if !commands.is_empty() {
                    subpaths.push(ClosedSubpath {
                        commands: std::mem::take(&mut commands),
                        sample_points: std::mem::take(&mut sample_points),
                    });
                }
            }
        }
    }

    subpaths
}

fn subpath_to_svg_string(subpath: &ClosedSubpath, precision: Option<u32>) -> String {
    let mut result = String::new();

    for command in &subpath.commands {
        match command {
            SubpathCommand::MoveTo { x, y } => {
                result.push_str(&format!(
                    "M{} {} ",
                    format_number(*x as f64, precision),
                    format_number(*y as f64, precision)
                ));
            }
            SubpathCommand::LineTo { x, y } => {
                result.push_str(&format!(
                    "L{} {} ",
                    format_number(*x as f64, precision),
                    format_number(*y as f64, precision)
                ));
            }
            SubpathCommand::QuadTo { cx, cy, x, y } => {
                result.push_str(&format!(
                    "Q{} {} {} {} ",
                    format_number(*cx as f64, precision),
                    format_number(*cy as f64, precision),
                    format_number(*x as f64, precision),
                    format_number(*y as f64, precision)
                ));
            }
            SubpathCommand::CubicTo {
                c1x,
                c1y,
                c2x,
                c2y,
                x,
                y,
            } => {
                result.push_str(&format!(
                    "C{} {} {} {} {} {} ",
                    format_number(*c1x as f64, precision),
                    format_number(*c1y as f64, precision),
                    format_number(*c2x as f64, precision),
                    format_number(*c2y as f64, precision),
                    format_number(*x as f64, precision),
                    format_number(*y as f64, precision)
                ));
            }
            SubpathCommand::Close => result.push_str("Z "),
        }
    }

    result
}

fn tiny_skia_path_to_svg_string(path: &resvg::tiny_skia::Path, precision: Option<u32>) -> String {
    let mut result = String::new();

    for segment in path.segments() {
        match segment {
            PathSegment::MoveTo(point) => {
                result.push_str(&format!(
                    "M{} {} ",
                    format_number(point.x as f64, precision),
                    format_number(point.y as f64, precision)
                ));
            }
            PathSegment::LineTo(point) => {
                result.push_str(&format!(
                    "L{} {} ",
                    format_number(point.x as f64, precision),
                    format_number(point.y as f64, precision)
                ));
            }
            PathSegment::QuadTo(control, point) => {
                result.push_str(&format!(
                    "Q{} {} {} {} ",
                    format_number(control.x as f64, precision),
                    format_number(control.y as f64, precision),
                    format_number(point.x as f64, precision),
                    format_number(point.y as f64, precision)
                ));
            }
            PathSegment::CubicTo(control1, control2, point) => {
                result.push_str(&format!(
                    "C{} {} {} {} {} {} ",
                    format_number(control1.x as f64, precision),
                    format_number(control1.y as f64, precision),
                    format_number(control2.x as f64, precision),
                    format_number(control2.y as f64, precision),
                    format_number(point.x as f64, precision),
                    format_number(point.y as f64, precision)
                ));
            }
            PathSegment::Close => result.push_str("Z "),
        }
    }

    result
}

fn format_number(num: f64, precision: Option<u32>) -> String {
    match precision {
        None => format!("{}", num),
        Some(0) => format!("{:.0}", num),
        Some(p) => {
            let mut string = format!("{:.1$}", num, p as usize);
            string = string.trim_end_matches('0').trim_end_matches('.').to_owned();
            string
        }
    }
}
